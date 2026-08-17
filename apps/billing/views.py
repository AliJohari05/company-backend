from decimal import Decimal
from mimetypes import guess_type
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, filters, exceptions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
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


def django_validation_details(error):
    if hasattr(error, 'message_dict'):
        return error.message_dict
    return {'non_field_errors': error.messages}


class FileDownloadContentNegotiation(DefaultContentNegotiation):
    """
    Let FileResponse determine the final content type.

    DRF's default negotiation would reject Accept headers such as
    application/pdf before the download view can return the file.
    """

    def select_renderer(self, request, renderers, format_suffix=None):
        renderer = renderers[0]
        return renderer, renderer.media_type


def private_file_response(field_file):
    if not field_file:
        raise exceptions.NotFound(_("File not found."))

    try:
        file_handle = field_file.open('rb')
    except (FileNotFoundError, OSError) as error:
        raise exceptions.NotFound(_("File not found.")) from error

    filename = PurePosixPath(field_file.name).name
    content_type = guess_type(filename)[0] or 'application/octet-stream'
    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=filename,
        content_type=content_type,
    )
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


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
        if getattr(self, 'swagger_fake_view', False):
            return Invoice.objects.none()

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
        if getattr(self, 'swagger_fake_view', False):
            return Invoice.objects.none()

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
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()

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
        try:
            serializer.save(user=invoice.user)
        except DjangoValidationError as error:
            raise exceptions.ValidationError(
                django_validation_details(error)
            ) from error


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
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()

        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all().select_related('invoice', 'user')
        return Transaction.objects.filter(user=user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not request.user.is_staff:
            raise exceptions.PermissionDenied(_("You do not have permission to modify this transaction."))

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as error:
            raise exceptions.ValidationError(
                django_validation_details(error)
            ) from error

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except DjangoValidationError as error:
            raise exceptions.ValidationError(
                django_validation_details(error)
            ) from error

    @db_transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        Invoice.objects.select_for_update().get(pk=instance.invoice_id)
        instance = Transaction.objects.select_for_update().get(pk=instance.pk)
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

    @db_transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        Invoice.objects.select_for_update().get(pk=instance.invoice_id)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        if getattr(self, 'swagger_fake_view', False):
            return Contract.objects.none()

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
        if getattr(self, 'swagger_fake_view', False):
            return Contract.objects.none()

        user = self.request.user
        if user.is_staff:
            return Contract.objects.all().select_related('user')
        return Contract.objects.filter(user=user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not request.user.is_staff:
            raise exceptions.PermissionDenied(_("You do not have permission to modify this contract."))


class ContractDownloadView(APIView):
    """Download a contract owned by the current user, or any contract as staff."""

    permission_classes = [permissions.IsAuthenticated]
    content_negotiation_class = FileDownloadContentNegotiation

    @extend_schema(responses={(200, 'application/pdf'): OpenApiTypes.BINARY})
    def get(self, request, pk):
        queryset = Contract.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)

        contract = get_object_or_404(queryset, pk=pk)
        return private_file_response(contract.file)


class TransactionReceiptDownloadView(APIView):
    """Download a payment receipt owned by the current user, or any as staff."""

    permission_classes = [permissions.IsAuthenticated]
    content_negotiation_class = FileDownloadContentNegotiation

    @extend_schema(
        responses={(200, 'application/octet-stream'): OpenApiTypes.BINARY}
    )
    def get(self, request, pk):
        queryset = Transaction.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)

        payment = get_object_or_404(queryset, pk=pk)
        return private_file_response(payment.receipt_attachment)


class PrivateBillingFileDownloadView(APIView):
    """
    Authenticated storage URL used by Django Admin file widgets.

    React clients should use the resource-specific download endpoints instead.
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    content_negotiation_class = FileDownloadContentNegotiation

    @extend_schema(exclude=True)
    def get(self, request, file_path):
        path = PurePosixPath(file_path)
        if path.is_absolute() or '..' in path.parts:
            raise exceptions.NotFound(_("File not found."))

        normalized_path = path.as_posix()
        if normalized_path.startswith('contracts/'):
            queryset = Contract.objects.filter(file=normalized_path)
            field_name = 'file'
        elif normalized_path.startswith('receipts/'):
            queryset = Transaction.objects.filter(
                receipt_attachment=normalized_path
            )
            field_name = 'receipt_attachment'
        else:
            raise exceptions.NotFound(_("File not found."))

        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)

        instance = queryset.first()
        if instance is None:
            raise exceptions.NotFound(_("File not found."))

        return private_file_response(getattr(instance, field_name))


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

    @db_transaction.atomic
    def perform_create(self, serializer):
        invoice = serializer.validated_data['invoice']
        locked_invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        try:
            serializer.save(invoice=locked_invoice)
        except DjangoValidationError as error:
            raise exceptions.ValidationError(
                django_validation_details(error)
            ) from error


class InvoiceItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / DELETE: Manage specific invoice items (Admins only).
    """
    queryset = InvoiceItem.objects.all().select_related('invoice')
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAdminUser]

    @db_transaction.atomic
    def perform_update(self, serializer):
        invoice_id = serializer.instance.invoice_id
        Invoice.objects.select_for_update().get(pk=invoice_id)
        try:
            serializer.save()
        except DjangoValidationError as error:
            raise exceptions.ValidationError(
                django_validation_details(error)
            ) from error

    @db_transaction.atomic
    def perform_destroy(self, instance):
        Invoice.objects.select_for_update().get(pk=instance.invoice_id)
        try:
            instance.delete()
        except DjangoValidationError as error:
            raise exceptions.ValidationError(
                django_validation_details(error)
            ) from error
