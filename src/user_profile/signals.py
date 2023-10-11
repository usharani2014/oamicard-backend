from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import get_template

from user_profile.models import Connections, UserSettings

url = settings.CONNECTION_URL


@receiver(post_save, sender=Connections)
def send_email(sender, instance, created, **kwargs):
    if instance:
        if UserSettings.objects.filter(
            user=instance.profile.user, is_email_notifications_active=True
        ).exists():
            instance.profile.user.first_name = (
                instance.profile.user.first_name
            ).title()
            message = get_template("email_templates/connections.html").render(
                {"user": instance, "url": url}
            )
            mail = EmailMessage(
                subject="You Have A New Connection",
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[instance.profile.user.email],
            )
            mail.content_subtype = "html"
            return mail.send()


# @receiver(post_save, sender=UserProfile)
# def add_user_profile_analytics(sender, instance, created, **kwargs):
#     if created:
#         Analytics.objects.create(profile=instance)
