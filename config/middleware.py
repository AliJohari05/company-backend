from django.conf import settings
from django.utils import translation


class AdminLanguageMiddleware:
    """Keep admin English by default while honoring an explicit session choice."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_languages = {code for code, _ in settings.LANGUAGES}

    def __call__(self, request):
        if not request.path.startswith('/admin/'):
            return self.get_response(request)

        language = request.session.get(
            getattr(settings, 'LANGUAGE_SESSION_KEY', 'django_language'),
            settings.LANGUAGE_CODE,
        )
        if language not in self.allowed_languages:
            language = settings.LANGUAGE_CODE

        with translation.override(language):
            return self.get_response(request)
