from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.services.models import Service, ServiceCategory
from .models import ProjectAttachment, ProjectRequest, ProjectStatus


class ProjectAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.memory_storage = InMemoryStorage()
        cls.attachment_field = ProjectAttachment._meta.get_field('file')
        cls.original_storage = cls.attachment_field.storage
        cls.attachment_field.storage = cls.memory_storage

    @classmethod
    def tearDownClass(cls):
        cls.attachment_field.storage = cls.original_storage
        super().tearDownClass()

    def setUp(self):
        self.client_user = User.objects.create_user(
            email='project-client@example.com',
            password='StrongPass1!',
        )
        self.other_user = User.objects.create_user(
            email='project-other@example.com',
            password='StrongPass1!',
        )
        self.staff = User.objects.create_user(
            email='project-staff@example.com',
            password='StrongPass1!',
            is_staff=True,
        )
        category = ServiceCategory.objects.create(
            title='Web Development',
            slug='web-development',
        )
        self.service = Service.objects.create(
            category=category,
            title='Django Development',
            slug='django-development',
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_project(self, user=None, title='Company website'):
        self.authenticate(user or self.client_user)
        response = self.client.post(
            reverse('project_list_create'),
            {
                'service': self.service.pk,
                'title': title,
                'description': 'A complete company website.',
                'estimated_budget': '1000000.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_create_project_assigns_authenticated_user(self):
        response = self.create_project()
        self.assertEqual(response.data['user'], self.client_user.pk)
        self.assertEqual(response.data['status'], ProjectStatus.PENDING)

    def test_project_list_and_detail_are_owner_scoped(self):
        own_id = self.create_project().data['id']
        other_id = self.create_project(
            self.other_user,
            title='Other project',
        ).data['id']

        self.authenticate(self.client_user)
        list_response = self.client.get(reverse('project_list_create'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        result_ids = {
            str(item['id']) for item in list_response.data['results']
        }
        self.assertIn(str(own_id), result_ids)
        self.assertNotIn(str(other_id), result_ids)

        forbidden_detail = self.client.get(
            reverse('project_detail', kwargs={'pk': other_id})
        )
        self.assertEqual(
            forbidden_detail.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.authenticate(self.staff)
        staff_list = self.client.get(reverse('project_list_create'))
        staff_ids = {
            str(item['id']) for item in staff_list.data['results']
        }
        self.assertIn(str(own_id), staff_ids)
        self.assertIn(str(other_id), staff_ids)

    def test_attachment_upload_enforces_project_ownership(self):
        project_id = self.create_project().data['id']
        url = reverse(
            'project_attachment_create',
            kwargs={'project_id': project_id},
        )

        self.authenticate(self.other_user)
        forbidden_response = self.client.post(
            url,
            {
                'file': ContentFile(b'not allowed', name='other.txt'),
                'description': 'Other user attachment',
            },
            format='multipart',
        )
        self.assertEqual(
            forbidden_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.authenticate(self.client_user)
        response = self.client.post(
            url,
            {
                'file': ContentFile(b'project document', name='project.txt'),
                'description': 'Project document',
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ProjectAttachment.objects.filter(
                project_request_id=project_id
            ).exists()
        )

        staff_project = ProjectRequest.objects.create(
            user=self.other_user,
            service=self.service,
            title='Staff accessible project',
            description='Staff may attach files.',
        )
        self.authenticate(self.staff)
        staff_response = self.client.post(
            reverse(
                'project_attachment_create',
                kwargs={'project_id': staff_project.pk},
            ),
            {
                'file': ContentFile(b'staff document', name='staff.txt'),
                'description': 'Staff attachment',
            },
            format='multipart',
        )
        self.assertEqual(staff_response.status_code, status.HTTP_201_CREATED)
