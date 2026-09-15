from django.core.management.base import BaseCommand

from apps.billing.models import refresh_expired_statuses


class Command(BaseCommand):
    help = "Mark overdue invoices and expired contracts based on their dates."

    def handle(self, *args, **options):
        refresh_expired_statuses()
        self.stdout.write(self.style.SUCCESS("Billing statuses refreshed."))
