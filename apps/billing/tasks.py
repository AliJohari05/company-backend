from celery import shared_task

from .models import refresh_expired_statuses


@shared_task
def refresh_billing_statuses():
    refresh_expired_statuses()
