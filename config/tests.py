from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from django.utils.translation import get_language

from .middleware import AdminLanguageMiddleware


class OpenAPISchemaTests(SimpleTestCase):
    def test_operations_expose_accept_language_header(self):
        response = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )
        self.assertEqual(response.status_code, 200)

        schema = response.json()
        operations = [
            operation
            for path_item in schema["paths"].values()
            for method, operation in path_item.items()
            if method in {"get", "post", "put", "patch", "delete"}
        ]
        self.assertTrue(operations)

        for operation in operations:
            language_parameters = [
                parameter
                for parameter in operation.get("parameters", [])
                if parameter.get("name") == "Accept-Language"
                and parameter.get("in") == "header"
            ]
            self.assertEqual(len(language_parameters), 1)
            self.assertEqual(
                language_parameters[0]["schema"]["enum"],
                ["en", "fa"],
            )


class AdminLanguageMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _response_language(self, request):
        middleware = AdminLanguageMiddleware(
            lambda current_request: JsonResponse({"language": get_language()})
        )
        return (
            middleware(request)
            .content.decode("utf-8")
            .split('"language": "')[1]
            .split('"')[0]
        )

    def test_admin_defaults_to_english(self):
        request = self.factory.get(
            "/admin/login/",
            HTTP_ACCEPT_LANGUAGE="fa",
        )
        SessionMiddleware(lambda _: None).process_request(request)
        self.assertEqual(self._response_language(request), "en")

    def test_admin_honors_explicit_session_language(self):
        request = self.factory.get("/admin/login/")
        SessionMiddleware(lambda _: None).process_request(request)
        request.session["django_language"] = "fa"
        self.assertEqual(self._response_language(request), "fa")
