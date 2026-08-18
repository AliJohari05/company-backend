from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import build_verification_url
from .models import User
from .tokens import email_verification_token


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_URL='https://frontend.example.com',
)
class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='account-user@example.com',
            password='OldStrong1!',
            first_name='Initial',
        )

    def test_register_creates_client_user(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('auth_register'),
                {
                    'email': 'New-Client@Example.COM',
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
        self.assertFalse(created_user.is_active)
        self.assertFalse(created_user.is_email_verified)
        self.assertIsNone(created_user.email_verified_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [created_user.email])
        self.assertIn(
            'https://frontend.example.com/verify-email?',
            mail.outbox[0].body,
        )
        self.assertEqual(len(mail.outbox[0].alternatives), 1)

    def test_registered_user_can_verify_email_and_then_login(self):
        with self.captureOnCommitCallbacks(execute=True):
            register_response = self.client.post(
                reverse('auth_register'),
                {
                    'email': 'verify-me@example.com',
                    'password': 'StrongPass1!',
                    'password_confirm': 'StrongPass1!',
                },
                format='json',
            )
        self.assertEqual(
            register_response.status_code,
            status.HTTP_201_CREATED,
        )
        user = User.objects.get(email='verify-me@example.com')
        verification_query = parse_qs(
            urlparse(build_verification_url(user)).query
        )

        verify_response = self.client.post(
            reverse('verify_email'),
            {
                'uid': verification_query['uid'][0],
                'token': verification_query['token'][0],
            },
            format='json',
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertIsNotNone(user.email_verified_at)

        login_response = self.client.post(
            reverse('token_obtain_pair'),
            {
                'email': user.email,
                'password': 'StrongPass1!',
            },
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)

    def test_unverified_user_cannot_login(self):
        user = User.objects.create_user(
            email='inactive-unverified@example.com',
            password='StrongPass1!',
            is_active=False,
            is_email_verified=False,
        )
        response = self.client.post(
            reverse('token_obtain_pair'),
            {
                'email': user.email,
                'password': 'StrongPass1!',
            },
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_verify_rejects_invalid_and_expired_tokens(self):
        user = User.objects.create_user(
            email='token-test@example.com',
            password='StrongPass1!',
            is_active=False,
        )
        query = parse_qs(urlparse(build_verification_url(user)).query)

        invalid_response = self.client.post(
            reverse('verify_email'),
            {
                'uid': query['uid'][0],
                'token': 'invalid-token',
            },
            format='json',
        )
        self.assertEqual(
            invalid_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        issued_at = datetime(2026, 8, 18, 9, 0, 0)
        with patch.object(
            email_verification_token,
            '_now',
            return_value=issued_at,
        ):
            expired_token = email_verification_token.make_token(user)
        with patch.object(
            email_verification_token,
            '_now',
            return_value=issued_at + timedelta(days=2),
        ):
            expired_response = self.client.post(
                reverse('verify_email'),
                {
                    'uid': query['uid'][0],
                    'token': expired_token,
                },
                format='json',
            )
        self.assertEqual(
            expired_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)

    def test_verification_never_reactivates_suspended_verified_user(self):
        suspended_user = User.objects.create_user(
            email='suspended@example.com',
            password='StrongPass1!',
            is_active=False,
            is_email_verified=True,
        )
        query = parse_qs(
            urlparse(build_verification_url(suspended_user)).query
        )
        response = self.client.post(
            reverse('verify_email'),
            {
                'uid': query['uid'][0],
                'token': query['token'][0],
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suspended_user.refresh_from_db()
        self.assertFalse(suspended_user.is_active)
        self.assertTrue(suspended_user.is_email_verified)

    def test_resend_response_does_not_reveal_account_existence(self):
        unverified_user = User.objects.create_user(
            email='resend@example.com',
            password='StrongPass1!',
            is_active=False,
            is_email_verified=False,
        )

        with self.captureOnCommitCallbacks(execute=True):
            existing_response = self.client.post(
                reverse('resend_verification'),
                {'email': unverified_user.email},
                format='json',
            )
        self.assertEqual(existing_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        with self.captureOnCommitCallbacks(execute=True):
            missing_response = self.client.post(
                reverse('resend_verification'),
                {'email': 'missing@example.com'},
                format='json',
            )
        self.assertEqual(missing_response.status_code, status.HTTP_200_OK)
        self.assertEqual(existing_response.data, missing_response.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_verified_account_does_not_receive_verification_resend(self):
        verified_user = User.objects.create_user(
            email='already-verified@example.com',
            password='StrongPass1!',
            is_email_verified=True,
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('resend_verification'),
                {'email': verified_user.email},
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_registration_rejects_case_insensitive_duplicate_email(self):
        User.objects.create_user(
            email='duplicate@example.com',
            password='StrongPass1!',
        )
        response = self.client.post(
            reverse('auth_register'),
            {
                'email': 'DUPLICATE@EXAMPLE.COM',
                'password': 'StrongPass1!',
                'password_confirm': 'StrongPass1!',
            },
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_accept_language_fa_translates_api_and_verification_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('auth_register'),
                {
                    'email': 'persian-user@example.com',
                    'first_name': 'علی',
                    'password': 'StrongPass1!',
                    'password_confirm': 'StrongPass1!',
                },
                format='json',
                HTTP_ACCEPT_LANGUAGE='fa',
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['detail'],
            'ثبت‌نام با موفقیت انجام شد. لطفاً آدرس ایمیل خود را تأیید کنید.',
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'آدرس ایمیل حساب CtrlOps خود را تأیید کنید',
        )
        self.assertIn('سلام علی،', mail.outbox[0].body)
        html_body = mail.outbox[0].alternatives[0][0]
        self.assertIn('lang="fa"', html_body)
        self.assertIn('dir="rtl"', html_body)

    def test_accept_language_en_remains_default(self):
        response = self.client.post(
            reverse('verify_email'),
            {'uid': 'invalid', 'token': 'invalid'},
            format='json',
            HTTP_ACCEPT_LANGUAGE='en',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'The verification link is invalid or has expired.',
        )

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
