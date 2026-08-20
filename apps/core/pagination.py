from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """standard pagination for API responses"""

    page_size = 10
    page_size_query_param = (
        "page_size"  # Allow clients to override the page size via query parameters.
    )
    max_page_size = 100


class BlogPostsPagination(PageNumberPagination):
    """blog post pagination"""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 30


class InvoiceListPagination(PageNumberPagination):
    """invoice and transaction list pagination"""

    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50
