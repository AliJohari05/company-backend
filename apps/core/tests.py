from django.urls import reverse
from unittest.mock import patch

from django.db import DatabaseError
from rest_framework import status
from rest_framework.test import APITestCase

from .models import FAQ, SiteSetting, SocialLink


class CoreAPITests(APITestCase):
    def setUp(self):
        self.active_link = SocialLink.objects.create(
            title='GitHub',
            url='https://github.com/ctrlops',
        )
        SocialLink.objects.create(
            title='Inactive',
            url='https://example.com/inactive',
            is_active=False,
        )
        self.second_faq = FAQ.objects.create(
            question='Second question?',
            answer='Second answer.',
            order=2,
        )
        self.first_faq = FAQ.objects.create(
            question='First question?',
            answer='First answer.',
            order=1,
        )
        FAQ.objects.create(
            question='Inactive question?',
            answer='Hidden answer.',
            is_active=False,
        )

    def test_site_settings_are_public_and_include_active_social_links(self):
        response = self.client.get(reverse('core:site-settings'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SiteSetting.objects.count(), 1)
        social_ids = {item['id'] for item in response.data['social_links']}
        self.assertEqual(social_ids, {self.active_link.pk})

    def test_social_link_list_only_contains_active_links(self):
        response = self.client.get(reverse('core:social-links-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertEqual(result_ids, {self.active_link.pk})

    def test_faq_list_is_active_and_ordered(self):
        response = self.client.get(reverse('core:faq-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertEqual(
            result_ids,
            [self.first_faq.pk, self.second_faq.pk],
        )

    def test_health_check_reports_database_readiness(self):
        response = self.client.get(reverse('health-check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {'status': 'ok', 'database': 'ok'},
        )

    @patch(
        'apps.core.views.connection.cursor',
        side_effect=DatabaseError('database unavailable'),
    )
    def test_health_check_returns_503_when_database_is_unavailable(
        self,
        mocked_cursor,
    ):
        response = self.client.get(reverse('health-check'))
        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(response.json()['status'], 'unhealthy')
