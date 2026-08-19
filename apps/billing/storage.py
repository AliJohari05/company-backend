from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateBillingStorage(FileSystemStorage):
    """Local storage whose URLs are served only by authenticated API views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", settings.PRIVATE_MEDIA_ROOT)
        kwargs.setdefault("base_url", settings.PRIVATE_MEDIA_URL)
        super().__init__(*args, **kwargs)


private_billing_storage = PrivateBillingStorage()
