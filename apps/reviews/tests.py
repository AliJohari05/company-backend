from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.blog.models import Post
from apps.services.models import Service, ServiceCategory

from .models import Review


class ReviewAPITests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="review-client@example.com", password="StrongPass1!")
        self.other_user = User.objects.create_user(email="review-other@example.com", password="StrongPass1!")
        self.staff = User.objects.create_user(email="review-staff@example.com", password="StrongPass1!", is_staff=True)
        category = ServiceCategory.objects.create(title="Development", slug="development")
        self.service = Service.objects.create(category=category, title="API", slug="api")
        self.post = Post.objects.create(author=self.staff, title="Article", content="Content", slug="article", is_published=True)

    def url(self, name="review-list-create", **kwargs):
        return reverse(name, kwargs=kwargs)

    def test_anonymous_can_list_but_cannot_create(self):
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_200_OK)
        response = self.client.post(self.url(), {"post": self.post.pk, "content": "Nice", "rating": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_is_pending_and_staff_reply_is_approved(self):
        self.client.force_authenticate(self.client_user)
        response = self.client.post(self.url(), {"post": self.post.pk, "content": "Nice", "rating": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get(pk=response.data["id"])
        self.assertFalse(review.is_approved)

        self.client.force_authenticate(self.staff)
        reply = self.client.post(self.url("review-reply", pk=review.pk), {"content": "Thank you"}, format="json")
        self.assertEqual(reply.status_code, status.HTTP_201_CREATED)
        answer = Review.objects.get(pk=reply.data["id"])
        self.assertTrue(answer.is_approved)
        self.assertEqual(answer.parent_id, review.pk)

    def test_only_staff_can_reply_and_target_is_exclusive(self):
        self.client.force_authenticate(self.client_user)
        response = self.client.post(self.url(), {"post": self.post.pk, "service": self.service.pk, "content": "Invalid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        review = Review.objects.create(user=self.client_user, post=self.post, content="Pending")
        response = self.client.post(self.url("review-reply", pk=review.pk), {"content": "No"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

