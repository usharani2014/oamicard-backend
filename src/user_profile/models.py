import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models

from oamii_cards.models import DatetimeModel
from user_profile.validators import (
    validate_address,
    validate_email,
    validate_phone,
    validate_website,
)

phone_choices = (("work", "work"),)
video_source_choices = (("youtube", "youtube"), ("vimeo", "vimeo"))
link_types = (("website", "website"), ("review", "review"), ("social", "social"))
theme_choices = (("professional", "professional"), ("classic", "classic"))
analytics_choices = (
    ("profile_views", "profile_views"),
    ("saved_contacts", "saved_contacts"),
    ("exchanged_contacts", "exchanged_contacts"),
)


class CountryCode(DatetimeModel):
    country = models.CharField(max_length=50, unique=True)
    country_code = models.CharField(max_length=10)


class Providers(DatetimeModel):
    title = models.CharField(max_length=20, unique=True)
    icon = models.FileField(
        upload_to="icons", validators=[FileExtensionValidator(["jpg", "png", "svg"])]
    )


class UserProfile(DatetimeModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(blank=True, max_length=50, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile_name = models.CharField(max_length=50, unique=True)
    company_name = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    bio_details = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile")
    position = models.CharField(max_length=20)
    phone = models.JSONField(validators=[validate_phone], default=list)
    email = models.JSONField(validators=[validate_email], default=list)
    website = models.JSONField(validators=[validate_website], default=list)
    address = models.JSONField(validators=[validate_address], default=list)
    is_active = models.BooleanField(default=False)


class Video(DatetimeModel):
    profile = models.OneToOneField("UserProfile", on_delete=models.CASCADE)
    video_source = models.CharField(
        max_length=15, choices=video_source_choices, default="youtube"
    )
    video_url = models.URLField(max_length=200)
    video_description = models.CharField(max_length=1000)


class Links(DatetimeModel):
    profile = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    types = models.CharField(max_length=30, choices=link_types)
    url = models.URLField(max_length=200)
    provider = models.ForeignKey("Providers", on_delete=models.CASCADE, null=True)
    meta = models.JSONField()  # Add title for the website links
    position = models.IntegerField(null=True, blank=True)  # for The up/down arrows.
    is_deleted = models.BooleanField(default=False)


class Analytics(DatetimeModel):
    profile = models.ForeignKey(
        "UserProfile",
        on_delete=models.CASCADE,
    )
    analytics_type = models.CharField(max_length=30, choices=analytics_choices)
    ip_address = models.GenericIPAddressField()


class UserSettings(DatetimeModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_email_notifications_active = models.BooleanField(default=True)
    theme = models.CharField(
        max_length=15, choices=theme_choices, default="professional"
    )
    theme_color = models.CharField(max_length=7, default="#023458")


class Connections(DatetimeModel):
    profile = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    company_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "email"], name="unique contact email"
            ),
            models.UniqueConstraint(
                fields=["profile", "contact_number"],
                name="unique contact contact number",
            ),
        ]


class Card(DatetimeModel):
    card = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card_serial_no = models.IntegerField(
        verbose_name="card_serial_no", unique=True, null=True, editable=False
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    printed = models.BooleanField(default=False)
    assigned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    label = models.CharField(null=True, blank=True, max_length=100)

    @property
    def card_link(self):
        url = settings.PROFILE_QRCODE_URL
        return f"{url}" + str(self.card)

    @property
    def card_number(self):
        return self.card_serial_no


class ProfileCards(DatetimeModel):
    data = models.JSONField()
    profile = models.OneToOneField("UserProfile", on_delete=models.CASCADE)
