from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token


def build_verification_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    query = urlencode({'uid': uid, 'token': token})
    return f'{settings.FRONTEND_URL}/verify-email?{query}'


def send_verification_email(user):
    context = {
        'user': user,
        'verification_url': build_verification_url(user),
        'expires_in_hours': max(
            1,
            settings.EMAIL_VERIFICATION_TIMEOUT // 3600,
        ),
    }
    subject = ''.join(
        render_to_string(
            'emails/accounts/verify_email_subject.txt',
            context,
        ).splitlines()
    )
    text_body = render_to_string(
        'emails/accounts/verify_email.txt',
        context,
    )
    html_body = render_to_string(
        'emails/accounts/verify_email.html',
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, 'text/html')
    return email.send()
