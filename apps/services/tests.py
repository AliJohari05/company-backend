from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Service, ServiceCategory, ServicePlan


class ServiceAPITests(APITestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            title="Development",
            slug="development",
        )
        self.inactive_category = ServiceCategory.objects.create(
            title="Inactive category",
            slug="inactive-category",
            is_active=False,
        )
        self.active_service = Service.objects.create(
            category=self.category,
            title="Django API",
            slug="django-api",
            short_description="Backend development",
            full_description="Professional automation platform",
        )
        self.inactive_service = Service.objects.create(
            category=self.category,
            title="Legacy service",
            slug="legacy-service",
            is_active=False,
        )
        ServicePlan.objects.create(
            service=self.active_service,
            title="Professional",
            price=Decimal("2500.00"),
            features=["API", "Support"],
        )

    def test_service_list_excludes_inactive_and_supports_search(self):
        response = self.client.get(reverse("service_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.active_service.pk, result_ids)
        self.assertNotIn(self.inactive_service.pk, result_ids)

        search_response = self.client.get(
            reverse("service_list"),
            {"search": "automation"},
        )
        search_ids = {item["id"] for item in search_response.data["results"]}
        self.assertEqual(search_ids, {self.active_service.pk})

    def test_category_list_only_nests_active_services(self):
        response = self.client.get(reverse("category_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.category.pk, category_ids)
        self.assertNotIn(self.inactive_category.pk, category_ids)

        category_data = next(
            item for item in response.data["results"] if item["id"] == self.category.pk
        )
        nested_ids = {item["id"] for item in category_data["services"]}
        self.assertEqual(nested_ids, {self.active_service.pk})

    def test_detail_contains_plans_and_inactive_service_is_hidden(self):
        response = self.client.get(
            reverse(
                "service_detail",
                kwargs={"slug": self.active_service.slug},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["plans"]), 1)
        self.assertEqual(response.data["plans"][0]["title"], "Professional")

        inactive_response = self.client.get(
            reverse(
                "service_detail",
                kwargs={"slug": self.inactive_service.slug},
            )
        )
        self.assertEqual(
            inactive_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
