from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='account-user@example.com',
            password='OldStrong1!',
            first_name='Initial',
        )

    def test_register_creates_client_user(self):
        response = self.client.post(
            reverse('auth_register'),
            {
                'email': 'new-client@example.com',
                'first_name': 'New',
                'last_name': 'Client',
                'password': 'StrongPass1!',
                'password_confirm': 'StrongPass1!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(email='new-client@example.com')
        self.assertTrue(created_user.check_password('StrongPass1!'))

    def test_profile_requires_authentication_and_updates_current_user(self):
        url = reverse('user_profile')
        anonymous_response = self.client.get(url)
        self.assertEqual(
            anonymous_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            url,
            {'first_name': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_change_password_checks_old_password(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('change_password')

        wrong_response = self.client.post(
            url,
            {
                'old_password': 'WrongPass1!',
                'new_password': 'NewStrong1!',
            },
            format='json',
        )
        self.assertEqual(
            wrong_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        response = self.client.post(
            url,
            {
                'old_password': 'OldStrong1!',
                'new_password': 'NewStrong1!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrong1!'))

    def test_logout_validates_and_blacklists_refresh_token(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('auth_logout')

        missing_response = self.client.post(url, {}, format='json')
        self.assertEqual(
            missing_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invalid_response = self.client.post(
            url,
            {'refresh': 'not-a-token'},
            format='json',
        )
        self.assertEqual(
            invalid_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            url,
            {'refresh': str(refresh)},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_205_RESET_CONTENT,
        )
