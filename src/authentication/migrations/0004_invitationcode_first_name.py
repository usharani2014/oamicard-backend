# Generated by Django 4.1.3 on 2023-01-24 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_alter_invitationcode_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="invitationcode",
            name="first_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]