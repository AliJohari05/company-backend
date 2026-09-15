from datetime import date, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Contract, Invoice, InvoiceItem, Transaction


class BillingAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.memory_storage = InMemoryStorage(base_url="/api/v1/billing/private-files/")
        cls.contract_file_field = Contract._meta.get_field("file")
        cls.receipt_file_field = Transaction._meta.get_field("receipt_attachment")
        cls.original_contract_storage = cls.contract_file_field.storage
        cls.original_receipt_storage = cls.receipt_file_field.storage
        cls.contract_file_field.storage = cls.memory_storage
        cls.receipt_file_field.storage = cls.memory_storage

    @classmethod
    def tearDownClass(cls):
        cls.contract_file_field.storage = cls.original_contract_storage
        cls.receipt_file_field.storage = cls.original_receipt_storage
        super().tearDownClass()

    def setUp(self):
        self.staff = User.objects.create_user(
            email="billing-staff@example.com",
            password="StrongPass1!",
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            email="billing-client@example.com",
            password="StrongPass1!",
        )
        self.other_user = User.objects.create_user(
            email="billing-other@example.com",
            password="StrongPass1!",
        )
        self.invoice = Invoice.objects.create(
            invoice_number="INV-TEST-001",
            user=self.client_user,
            due_date=date.today() + timedelta(days=10),
        )
        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Development",
            quantity=2,
            unit_price=Decimal("500.00"),
        )
        self.invoice.refresh_from_db()

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_invoice_total_recalculates_after_item_crud(self):
        self.assertEqual(self.invoice.total_amount, Decimal("1000.00"))
        self.authenticate(self.staff)

        create_response = self.client.post(
            reverse("billing:invoice-item-list-create"),
            {
                "invoice": self.invoice.pk,
                "description": "SEO",
                "quantity": 1,
                "unit_price": "250.00",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total_amount, Decimal("1250.00"))

        item_id = create_response.data["id"]
        update_response = self.client.patch(
            reverse("billing:invoice-item-detail", kwargs={"pk": item_id}),
            {"quantity": 2},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total_amount, Decimal("1500.00"))

        delete_response = self.client.delete(
            reverse("billing:invoice-item-detail", kwargs={"pk": item_id})
        )
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total_amount, Decimal("1000.00"))

    def test_transaction_creation_validates_owner_amount_and_reference(self):
        self.authenticate(self.client_user)
        url = reverse("billing:transaction-list-create")

        response = self.client.post(
            url,
            {
                "invoice": self.invoice.pk,
                "amount": "400.00",
                "reference_code": "TRACK-001",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice_number"], "INV-TEST-001")
        self.assertEqual(response.data["amount"], "400.00")

        duplicate_response = self.client.post(
            url,
            {
                "invoice": self.invoice.pk,
                "amount": "100.00",
                "reference_code": "TRACK-001",
            },
            format="json",
        )
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        excessive_response = self.client.post(
            url,
            {
                "invoice": self.invoice.pk,
                "amount": "1001.00",
                "reference_code": "TRACK-002",
            },
            format="json",
        )
        self.assertEqual(
            excessive_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.authenticate(self.other_user)
        forbidden_invoice_response = self.client.post(
            url,
            {
                "invoice": self.invoice.pk,
                "amount": "100.00",
                "reference_code": "TRACK-003",
            },
            format="json",
        )
        self.assertEqual(
            forbidden_invoice_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.authenticate(self.client_user)
        first_pending = self.client.post(
            url,
            {"invoice": self.invoice.pk, "amount": "500.00", "reference_code": "TRACK-004"},
            format="json",
        )
        self.assertEqual(first_pending.status_code, status.HTTP_201_CREATED)
        over_committed = self.client.post(
            url,
            {"invoice": self.invoice.pk, "amount": "200.00", "reference_code": "TRACK-005"},
            format="json",
        )
        self.assertEqual(over_committed.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_number_is_generated_and_dates_refresh_statuses(self):
        generated = Invoice.objects.create(
            user=self.client_user,
            due_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(generated.invoice_number.startswith("INV-"))

        contract = Contract.objects.create(
            user=self.client_user,
            title="Expired contract",
            file=ContentFile(b"%PDF-1.4", name="expired.pdf"),
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
        )
        self.authenticate(self.client_user)
        self.client.get(reverse("billing:invoice-list-create"))
        self.client.get(reverse("billing:contract-list-create"))
        generated.refresh_from_db()
        contract.refresh_from_db()
        self.assertEqual(generated.status, Invoice.StatusChoices.OVERDUE)
        self.assertEqual(contract.status, Contract.StatusChoices.EXPIRED)

    def test_approval_updates_invoice_and_locks_items(self):
        payment = Transaction.objects.create(
            invoice=self.invoice,
            user=self.client_user,
            amount=Decimal("400.00"),
            reference_code="TRACK-APPROVE",
        )
        self.authenticate(self.staff)

        approve_response = self.client.patch(
            reverse(
                "billing:transaction-detail",
                kwargs={"pk": payment.pk},
            ),
            {"status": Transaction.StatusChoices.APPROVED},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(
            self.invoice.status,
            Invoice.StatusChoices.PARTIALLY_PAID,
        )

        locked_update = self.client.patch(
            reverse(
                "billing:invoice-item-detail",
                kwargs={"pk": self.item.pk},
            ),
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(
            locked_update.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        reject_response = self.client.patch(
            reverse(
                "billing:transaction-detail",
                kwargs={"pk": payment.pk},
            ),
            {"status": Transaction.StatusChoices.REJECTED},
            format="json",
        )
        self.assertEqual(reject_response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.StatusChoices.UNPAID)

    def test_private_contract_download_permissions(self):
        contract = Contract.objects.create(
            user=self.client_user,
            title="Private contract",
            file=ContentFile(b"%PDF-1.4 test contract", name="contract.pdf"),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        detail_url = reverse(
            "billing:contract-detail",
            kwargs={"pk": contract.pk},
        )
        download_url = reverse(
            "billing:contract-download",
            kwargs={"pk": contract.pk},
        )

        self.authenticate(self.client_user)
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertNotIn("file", detail_response.data)
        self.assertEqual(
            detail_response.data["download_url"],
            f"http://testserver{download_url}",
        )

        owner_download = self.client.get(
            download_url,
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(owner_download.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_download["Content-Type"], "application/pdf")

        self.authenticate(self.other_user)
        other_download = self.client.get(download_url)
        self.assertEqual(other_download.status_code, status.HTTP_404_NOT_FOUND)

        self.authenticate(self.staff)
        staff_download = self.client.get(download_url)
        self.assertEqual(staff_download.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)
        anonymous_download = self.client.get(download_url)
        self.assertEqual(
            anonymous_download.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_private_receipt_download_permissions(self):
        payment = Transaction.objects.create(
            invoice=self.invoice,
            user=self.client_user,
            amount=Decimal("200.00"),
            reference_code="TRACK-FILE",
            receipt_attachment=ContentFile(
                b"\xff\xd8\xff test image",
                name="receipt.jpg",
            ),
        )
        download_url = reverse(
            "billing:transaction-receipt-download",
            kwargs={"pk": payment.pk},
        )

        self.authenticate(self.client_user)
        owner_response = self.client.get(
            download_url,
            HTTP_ACCEPT="application/octet-stream",
        )
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_response["Content-Type"], "image/jpeg")

        self.authenticate(self.other_user)
        other_response = self.client.get(download_url)
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)
