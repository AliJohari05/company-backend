from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Ticket, TicketMessage, TicketStatus


class TicketAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.memory_storage = InMemoryStorage()
        cls.attachment_field = TicketMessage._meta.get_field("attachment")
        cls.original_storage = cls.attachment_field.storage
        cls.attachment_field.storage = cls.memory_storage

    @classmethod
    def tearDownClass(cls):
        cls.attachment_field.storage = cls.original_storage
        super().tearDownClass()

    def setUp(self):
        self.client_user = User.objects.create_user(
            email="ticket-client@example.com",
            password="StrongPass1!",
        )
        self.other_user = User.objects.create_user(
            email="ticket-other@example.com",
            password="StrongPass1!",
        )
        self.staff = User.objects.create_user(
            email="ticket-staff@example.com",
            password="StrongPass1!",
            is_staff=True,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_ticket(self, user=None):
        self.authenticate(user or self.client_user)
        response = self.client.post(
            reverse("tickets:ticket-list-create"),
            {
                "title": "Website support",
                "priority": "MEDIUM",
                "message": "Please investigate this issue.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_create_ticket_returns_initial_message(self):
        response = self.create_ticket()
        self.assertEqual(response.data["user"], self.client_user.pk)
        self.assertEqual(response.data["status"], TicketStatus.OPEN)
        self.assertEqual(len(response.data["messages"]), 1)
        self.assertEqual(
            response.data["messages"][0]["message"],
            "Please investigate this issue.",
        )

    def test_ticket_list_and_detail_are_owner_scoped(self):
        own_ticket = self.create_ticket().data["id"]
        other_ticket = self.create_ticket(self.other_user).data["id"]

        self.authenticate(self.client_user)
        list_response = self.client.get(reverse("tickets:ticket-list-create"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        result_ids = {item["id"] for item in list_response.data["results"]}
        self.assertIn(own_ticket, result_ids)
        self.assertNotIn(other_ticket, result_ids)

        forbidden_detail = self.client.get(
            reverse("tickets:ticket-detail", kwargs={"pk": other_ticket})
        )
        self.assertEqual(
            forbidden_detail.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.authenticate(self.staff)
        staff_list = self.client.get(reverse("tickets:ticket-list-create"))
        staff_ids = {item["id"] for item in staff_list.data["results"]}
        self.assertIn(own_ticket, staff_ids)
        self.assertIn(other_ticket, staff_ids)

    def test_client_can_close_and_reopen_but_not_resolve(self):
        ticket_id = self.create_ticket().data["id"]
        url = reverse(
            "tickets:ticket-status-update",
            kwargs={"pk": ticket_id},
        )

        close_response = self.client.post(
            url,
            {"status": TicketStatus.CLOSED},
            format="json",
        )
        self.assertEqual(close_response.status_code, status.HTTP_200_OK)

        duplicate_close = self.client.post(
            url,
            {"status": TicketStatus.CLOSED},
            format="json",
        )
        self.assertEqual(
            duplicate_close.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        reopen_response = self.client.post(
            url,
            {"status": TicketStatus.OPEN},
            format="json",
        )
        self.assertEqual(reopen_response.status_code, status.HTTP_200_OK)

        resolve_response = self.client.post(
            url,
            {"status": TicketStatus.RESOLVED},
            format="json",
        )
        self.assertEqual(
            resolve_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_can_resolve_and_messages_update_workflow(self):
        ticket_id = self.create_ticket().data["id"]
        message_url = reverse(
            "tickets:ticket-message-create",
            kwargs={"ticket_id": ticket_id},
        )

        self.authenticate(self.staff)
        staff_message = self.client.post(
            message_url,
            {"message": "We are working on it."},
            format="json",
        )
        self.assertEqual(staff_message.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", staff_message.data)
        ticket = Ticket.objects.get(pk=ticket_id)
        self.assertEqual(ticket.status, TicketStatus.ANSWERED)

        self.authenticate(self.client_user)
        client_message = self.client.post(
            message_url,
            {"message": "Thank you."},
            format="json",
        )
        self.assertEqual(client_message.status_code, status.HTTP_201_CREATED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, TicketStatus.PENDING)

        self.authenticate(self.staff)
        resolve_response = self.client.post(
            reverse(
                "tickets:ticket-status-update",
                kwargs={"pk": ticket_id},
            ),
            {"status": TicketStatus.RESOLVED},
            format="json",
        )
        self.assertEqual(resolve_response.status_code, status.HTTP_200_OK)

        self.client.post(
            reverse(
                "tickets:ticket-status-update",
                kwargs={"pk": ticket_id},
            ),
            {"status": TicketStatus.CLOSED},
            format="json",
        )
        self.authenticate(self.client_user)
        closed_message = self.client.post(
            message_url,
            {"message": "This must be rejected."},
            format="json",
        )
        self.assertEqual(
            closed_message.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_ticket_attachment_download_is_private_and_owner_scoped(self):
        ticket = Ticket.objects.create(
            user=self.client_user,
            title="Private attachment",
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=self.client_user,
            message="Please inspect this private file.",
            attachment=ContentFile(
                b"private ticket document",
                name="ticket-private.txt",
            ),
        )
        detail_url = reverse(
            "tickets:ticket-detail",
            kwargs={"pk": ticket.pk},
        )
        download_url = reverse(
            "tickets:ticket-attachment-download",
            kwargs={"pk": message.pk},
        )

        self.authenticate(self.client_user)
        detail_response = self.client.get(detail_url)
        message_data = detail_response.data["messages"][0]
        self.assertNotIn("attachment", message_data)
        self.assertEqual(
            message_data["attachment_download_url"],
            f"http://testserver{download_url}",
        )

        owner_response = self.client.get(download_url)
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            owner_response["Cache-Control"],
            "private, no-store",
        )

        self.authenticate(self.other_user)
        other_response = self.client.get(download_url)
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

        self.authenticate(self.staff)
        staff_response = self.client.get(download_url)
        self.assertEqual(staff_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)
        anonymous_response = self.client.get(download_url)
        self.assertEqual(
            anonymous_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
