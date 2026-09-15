from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Generate one-time tokens invalidated after email verification."""

    def _make_hash_value(self, user, timestamp):
        return (
            f"{user.pk}{timestamp}{user.email}"
            f"{user.is_email_verified}{user.is_active}"
        )


email_verification_token = EmailVerificationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()
