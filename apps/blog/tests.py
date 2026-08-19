from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Category, Post, Tag


class BlogAPITests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="blog-staff@example.com",
            password="StrongPass1!",
            is_staff=True,
        )
        self.author = User.objects.create_user(
            email="blog-author@example.com",
            password="StrongPass1!",
        )
        self.other_user = User.objects.create_user(
            email="blog-other@example.com",
            password="StrongPass1!",
        )
        self.category = Category.objects.create(name="Django")
        self.tag = Tag.objects.create(name="Backend")
        self.published_post = Post.objects.create(
            author=self.author,
            title="Published article",
            content="Published content",
            category=self.category,
            is_published=True,
            published_at=timezone.now(),
        )
        self.published_post.tags.add(self.tag)
        self.draft_post = Post.objects.create(
            author=self.author,
            title="Draft article",
            content="Draft content",
            category=self.category,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_public_list_only_contains_published_posts(self):
        response = self.client.get(reverse("blog:post-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.published_post.pk, result_ids)
        self.assertNotIn(self.draft_post.pk, result_ids)

        self.authenticate(self.staff)
        staff_response = self.client.get(reverse("blog:post-list-create"))
        staff_ids = {item["id"] for item in staff_response.data["results"]}
        self.assertIn(self.published_post.pk, staff_ids)
        self.assertIn(self.draft_post.pk, staff_ids)

    def test_draft_detail_is_limited_to_author_and_staff(self):
        url = reverse(
            "blog:post-detail",
            kwargs={"slug": self.draft_post.slug},
        )
        anonymous_response = self.client.get(url)
        self.assertEqual(
            anonymous_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.authenticate(self.other_user)
        other_response = self.client.get(url)
        self.assertEqual(
            other_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.authenticate(self.author)
        author_response = self.client.get(url)
        self.assertEqual(author_response.status_code, status.HTTP_200_OK)

        self.authenticate(self.staff)
        staff_response = self.client.get(url)
        self.assertEqual(staff_response.status_code, status.HTTP_200_OK)

    def test_only_staff_can_create_posts_and_author_is_assigned(self):
        url = reverse("blog:post-list-create")
        payload = {
            "title": "API article",
            "content": "Created through the API.",
            "category": self.category.pk,
            "tags": [self.tag.pk],
            "is_published": False,
        }

        self.authenticate(self.author)
        forbidden_response = self.client.post(url, payload, format="json")
        self.assertEqual(
            forbidden_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.authenticate(self.staff)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_post = Post.objects.get(title="API article")
        self.assertEqual(created_post.author, self.staff)
        self.assertTrue(created_post.tags.filter(pk=self.tag.pk).exists())

    def test_author_permissions_and_view_counter(self):
        detail_url = reverse(
            "blog:post-detail",
            kwargs={"slug": self.published_post.slug},
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.views_count, 1)

        self.authenticate(self.other_user)
        forbidden_update = self.client.patch(
            detail_url,
            {"title": "Unauthorized edit"},
            format="json",
        )
        self.assertEqual(
            forbidden_update.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.authenticate(self.author)
        update_response = self.client.patch(
            detail_url,
            {"title": "Author edit"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.title, "Author edit")

    def test_category_and_tag_writes_are_staff_only(self):
        category_url = reverse("blog:category-list-create")
        tag_url = reverse("blog:tag-list-create")

        public_categories = self.client.get(category_url)
        self.assertEqual(public_categories.status_code, status.HTTP_200_OK)

        self.authenticate(self.author)
        forbidden_category = self.client.post(
            category_url,
            {"name": "Security"},
            format="json",
        )
        self.assertEqual(
            forbidden_category.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.authenticate(self.staff)
        category_response = self.client.post(
            category_url,
            {"name": "Security"},
            format="json",
        )
        tag_response = self.client.post(
            tag_url,
            {"name": "Testing"},
            format="json",
        )
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tag_response.status_code, status.HTTP_201_CREATED)
