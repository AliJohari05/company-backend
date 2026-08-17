from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Invoices
    path('invoices/', views.InvoiceListCreateView.as_view(), name='invoice-list-create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),

    # Invoice Items (Admin)
    path('invoice-items/', views.InvoiceItemListCreateView.as_view(), name='invoice-item-list-create'),
    path('invoice-items/<int:pk>/', views.InvoiceItemDetailView.as_view(), name='invoice-item-detail'),

    # Transactions / Receipts
    path('transactions/', views.TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path(
        'transactions/<int:pk>/receipt/',
        views.TransactionReceiptDownloadView.as_view(),
        name='transaction-receipt-download',
    ),

    # Contracts
    path('contracts/', views.ContractListCreateView.as_view(), name='contract-list-create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract-detail'),
    path(
        'contracts/<int:pk>/download/',
        views.ContractDownloadView.as_view(),
        name='contract-download',
    ),

    # Private storage URL used by authenticated clients and Django Admin.
    path(
        'private-files/<path:file_path>',
        views.PrivateBillingFileDownloadView.as_view(),
        name='private-file-download',
    ),
]
