from mimetypes import guess_type
from pathlib import PurePosixPath

from django.http import FileResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.negotiation import DefaultContentNegotiation


class FileDownloadContentNegotiation(DefaultContentNegotiation):
    """Allow FileResponse to choose the final binary content type."""

    def select_renderer(self, request, renderers, format_suffix=None):
        renderer = renderers[0]
        return renderer, renderer.media_type


def private_file_response(field_file):
    if not field_file:
        raise exceptions.NotFound(_("File not found."))

    filename = PurePosixPath(field_file.name).name
    content_type = guess_type(filename)[0] or "application/octet-stream"
    try:
        file_handle = field_file.open("rb")
    except (FileNotFoundError, OSError, ValueError) as error:
        raise exceptions.NotFound(_("File not found.")) from error

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=filename,
        content_type=content_type,
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
