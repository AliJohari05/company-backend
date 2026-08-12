from rest_framework import generics, permissions, filters, exceptions
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceItem, Transaction, Contract
from .serializers import (
    InvoiceSerializer,
    InvoiceItemSerializer,
    TransactionSerializer,
    ContractSerializer
)
from apps.core.pagination import InvoiceListPagination

# ==========================================
# INVOICE VIEWS
# ==========================================

class InvoiceListCreateView(generics.ListCreateAPIView):
    """
    GET: List invoices (Admins see all; regular users see only their own).
    POST: Create a new invoice (Admins only).
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['invoice_number']
    ordering_fields = ['created_at', 'due_date', 'total_amount']
    ordering = ['-created_at']
    pagination_class = InvoiceListPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Invoice.objects.all().select_related('user', 'project_request', 'service')
        return Invoice.objects.filter(user=user).select_related('user', 'project_request', 'service')

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise exceptions.PermissionDenied(_("Only administrators can generate invoices."))
        serializer.save()


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
            return Invoice.objects.all().select_related('user', 'project_request', 'service')
        return Invoice.objects.filter(user=user)

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
        # Ensure non-admin users can only attach transactions to their own invoices
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
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all().select_related('invoice', 'user')
        return Transaction.objects.filter(user=user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not request.user.is_staff:
            raise exceptions.PermissionDenied(_("You do not have permission to modify this transaction."))


# ==========================================
# CONTRACT VIEWS
# ==========================================

class ContractListCreateView(generics.ListCreateAPIView):
    """
    GET: List contracts (Admins see all; regular users see their own).
    POST: Create a new contract (Admins only).
    """
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['title']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Contract.objects.all().select_related('user')
        return Contract.objects.filter(user=user).select_related('user')

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise exceptions.PermissionDenied(_("Only administrators can upload or assign contracts."))
        serializer.save()


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