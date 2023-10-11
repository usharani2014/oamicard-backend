from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import get_template
from django_rest_passwordreset.signals import reset_password_token_created

from authentication.models import InvitationCode
from user_profile.models import User, UserSettings


@receiver(post_save, sender=User)
def send_email(sender, instance, created, **kwargs):
    user = {"first_name": instance.first_name, "email": instance.email}
    if created:
        user["first_name"] = user["first_name"].title()
        message = get_template("email_templates/welcome.html").render({"user": user})
        first_name = user.get("first_name").title()
        mail = EmailMessage(
            subject=f"{first_name}, Welcome to OamiiCards - Let's get started!",
            body=message,
            from_email=settings.EMAIL_HOST_USER,
            to=[instance.email],
        )
        mail.content_subtype = "html"
        return mail.send()


@receiver(post_save, sender=User)
def send_rest_password_email(sender, instance, created, **kwargs):
    user = {"first_name": instance.first_name, "email": instance.email}
    if not created:
        if UserSettings.objects.filter(
            user=instance.id, is_email_notifications_active=True
        ).exists():
            message = get_template("email_templates/reset_password.html").render(
                {
                    "user": user,
                    "link": (f"{settings.PASSWORD_FORGET_URL}"),
                }
            )
            mail = EmailMessage(
                subject="Your password was changed",
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[instance.email],
            )
            mail.content_subtype = "html"
            return mail.send()


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    email = instance.request.data.get("email")
    user = User.objects.filter(email=email).first()
    message = get_template("email_templates/forget_password_token.html").render(
        {
            "link": (f"{settings.PASSWORD_RESET_URL}?token={reset_password_token.key}"),
            "first_name": user.first_name,
        }
    )
    mail = EmailMessage(
        subject="Reset Password",
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[reset_password_token.user.email],
    )
    mail.content_subtype = "html"
    return mail.send()


@receiver(post_save, sender=User)
def add_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)


@receiver(post_save, sender=InvitationCode)
def send_otp(sender, instance, created, **kwargs):
    instance.first_name = (instance.first_name).title()
    if instance.code:
        message = get_template("email_templates/send_otp.html").render(
            {"otp": instance}
        )
        mail = EmailMessage(
            subject="OamiiCards - New User Sign up",
            body=message,
            from_email=settings.EMAIL_HOST_USER,
            to=[instance.email],
        )
        mail.content_subtype = "html"
        return mail.send()
