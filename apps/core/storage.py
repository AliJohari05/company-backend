from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """Filesystem storage exposed only through authenticated API views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", settings.PRIVATE_MEDIA_ROOT)
        kwargs.setdefault("base_url", settings.PRIVATE_UPLOAD_URL)
        super().__init__(*args, **kwargs)


private_media_storage = PrivateMediaStorage()
