from smtplib import SMTPException

from celery import shared_task
from django.contrib.auth import get_user_model

from .emails import send_password_reset_email, send_verification_email

User = get_user_model()


@shared_task(
    autoretry_for=(OSError, SMTPException),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_verification_email_task(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if not user.is_email_verified:
        send_verification_email(user)


@shared_task(
    autoretry_for=(OSError, SMTPException),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_password_reset_email_task(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if user.is_active and user.is_email_verified:
        send_password_reset_email(user)
