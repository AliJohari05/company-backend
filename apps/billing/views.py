from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, filters, exceptions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceItem, Transaction, Contract
from .serializers import (
    InvoiceSerializer,
    InvoiceItemSerializer,
    TransactionSerializer,
    TransactionStatusUpdateSerializer,
    ContractSerializer
)
from apps.core.pagination import InvoiceListPagination

# ==========================================
# INVOICE VIEWS
# ==========================================


def with_payment_summary(queryset):
    """Add the total of approved receipts to each invoice queryset."""
    return queryset.annotate(
        approved_amount=Coalesce(
            Sum(
                'transactions__amount',
                filter=Q(
                    transactions__status=Transaction.StatusChoices.APPROVED
                ),
            ),
            Value(Decimal('0.00')),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )


def refresh_invoice_payment_status(invoice):
    """Set an invoice status from the sum of approved payment receipts."""
    approved_amount = (
        invoice.transactions.filter(
            status=Transaction.StatusChoices.APPROVED
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    if approved_amount >= invoice.total_amount:
        new_status = Invoice.StatusChoices.PAID
    elif approved_amount > Decimal('0.00'):
        new_status = Invoice.StatusChoices.PARTIALLY_PAID
    else:
        new_status = Invoice.StatusChoices.UNPAID

    if invoice.status != new_status:
        invoice.status = new_status
        invoice.save(update_fields=['status', 'updated_at'])

class InvoiceListCreateView(generics.ListCreateAPIView):
    """
    GET: List invoices (Admins see all; regular users see only their own).
    POST: Create a new invoice (Admins only).
    """
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['invoice_number']
    ordering_fields = ['created_at', 'due_date', 'total_amount']
    ordering = ['-created_at']
    pagination_class = InvoiceListPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            queryset = Invoice.objects.all()
        else:
            queryset = Invoice.objects.filter(user=user)

        return with_payment_summary(
            queryset.select_related('user', 'project_request', 'service')
            .prefetch_related('items', 'transactions')
        )

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve invoice detail.
    PUT/PATCH/DELETE: Admin only.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            queryset = Invoice.objects.all()
        else:
            queryset = Invoice.objects.filter(user=user)

        return with_payment_summary(
            queryset.select_related('user', 'project_request', 'service')
            .prefetch_related('items', 'transactions')
        )

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not request.user.is_staff:
            raise exceptions.PermissionDenied(_("You do not have permission to modify this invoice."))


# ==========================================
# TRANSACTION / RECEIPT VIEWS
# ==========================================

class TransactionListCreateView(generics.ListCreateAPIView):
    """
    GET: List payment receipts (Admins see all; regular users see their own).
    POST: Upload a payment receipt for an invoice.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['invoice', 'status', 'user']
    search_fields = ['reference_code']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all().select_related('invoice', 'user')
        return Transaction.objects.filter(user=user).select_related('invoice', 'user')

    def perform_create(self, serializer):
        invoice = serializer.validated_data.get('invoice')
        if not self.request.user.is_staff and invoice.user != self.request.user:
            raise exceptions.ValidationError({
                "invoice": _("You can only submit payment receipts for your own invoices.")
            })
        serializer.save(user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve transaction details.
    PUT/PATCH/DELETE: Admin only.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TransactionStatusUpdateSerializer
        return TransactionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all().select_related('invoice', 'user')
        return Transaction.objects.filter(user=user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not request.user.is_staff:
            raise exceptions.PermissionDenied(_("You do not have permission to modify this transaction."))

    @db_transaction.atomic
    def perform_update(self, serializer):
        transaction = serializer.save()
        refresh_invoice_payment_status(transaction.invoice)

    @db_transaction.atomic
    def perform_destroy(self, instance):
        invoice = instance.invoice
        instance.delete()
        refresh_invoice_payment_status(invoice)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            TransactionSerializer(
                serializer.instance,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )


# ==========================================
# CONTRACT VIEWS
# ==========================================

class ContractListCreateView(generics.ListCreateAPIView):
    """
    GET: List contracts (Admins see all; regular users see their own).
    POST: Create a new contract (Admins only).
    """
    serializer_class = ContractSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['title']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Contract.objects.all().select_related('user')
        return Contract.objects.filter(user=user).select_related('user')

class ContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve contract details.
    PUT/PATCH/DELETE: Admin only.
    """
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Contract.objects.all().select_related('user')
        return Contract.objects.filter(user=user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not request.user.is_staff:
            raise exceptions.PermissionDenied(_("You do not have permission to modify this contract."))


# ==========================================
# INVOICE ITEM VIEWS (ADMIN ONLY)
# ==========================================

class InvoiceItemListCreateView(generics.ListCreateAPIView):
    """
    GET / POST: Manage individual items within invoices (Admins only).
    """
    queryset = InvoiceItem.objects.all().select_related('invoice')
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice']


class InvoiceItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / DELETE: Manage specific invoice items (Admins only).
    """
    queryset = InvoiceItem.objects.all().select_related('invoice')
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAdminUser]
