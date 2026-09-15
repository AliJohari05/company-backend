from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, PortfolioImage, PortfolioItem, Technology


class PortfolioAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.memory_storage = InMemoryStorage()
        cls.file_fields = [
            Technology._meta.get_field("icon"),
            PortfolioItem._meta.get_field("cover_image"),
            PortfolioImage._meta.get_field("image"),
        ]
        cls.original_storages = [field.storage for field in cls.file_fields]
        for field in cls.file_fields:
            field.storage = cls.memory_storage

    @classmethod
    def tearDownClass(cls):
        for field, storage in zip(
            cls.file_fields,
            cls.original_storages,
            strict=True,
        ):
            field.storage = storage
        super().tearDownClass()

    def setUp(self):
        self.category = Category.objects.create(
            title="Web applications",
            slug="web-applications",
        )
        self.technology = Technology.objects.create(name="Django")
        self.item = PortfolioItem.objects.create(
            title="CtrlOps platform",
            title_en="CtrlOps Platform",
            slug="ctrlops-platform",
            category=self.category,
            cover_image=ContentFile(b"cover", name="cover.jpg"),
            summary="Business automation platform",
            summary_en="Business automation platform in English",
            description="A complete Django and React project.",
            description_en="A complete Django and React project in English.",
            video_url="https://video.example.com/demo",
            is_featured=True,
        )
        self.item.technologies.add(self.technology)
        PortfolioImage.objects.create(
            portfolio=self.item,
            image=ContentFile(b"gallery", name="gallery.jpg"),
            caption="Dashboard",
        )

    def test_public_lists_support_filters_and_nested_data(self):
        category_response = self.client.get(reverse("portfolio:category-list"))
        self.assertEqual(category_response.status_code, status.HTTP_200_OK)

        list_response = self.client.get(
            reverse("portfolio:portfolio-list"),
            {"is_featured": "true", "technologies__name": "Django"},
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["results"]), 1)
        result = list_response.data["results"][0]
        self.assertEqual(result["id"], self.item.pk)
        self.assertEqual(result["category"]["slug"], self.category.slug)
        self.assertEqual(result["technologies"][0]["name"], "Django")

    def test_detail_contains_gallery_and_full_description(self):
        response = self.client.get(
            reverse(
                "portfolio:portfolio-detail",
                kwargs={"slug": self.item.slug},
            ),
            HTTP_ACCEPT_LANGUAGE="fa",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["description"],
            "A complete Django and React project.",
        )
        self.assertEqual(len(response.data["images"]), 1)
        self.assertEqual(response.data["images"][0]["caption"], "Dashboard")
        self.assertEqual(response.data["video_url"], "https://video.example.com/demo")

        english_response = self.client.get(
            reverse(
                "portfolio:portfolio-detail",
                kwargs={"slug": self.item.slug},
            ),
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(english_response.data["title"], "CtrlOps Platform")
        self.assertEqual(
            english_response.data["description"],
            "A complete Django and React project in English.",
        )
        self.assertNotIn("title_en", english_response.data)
