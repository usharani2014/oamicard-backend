# Generated by Django 4.1.3 on 2022-12-15 04:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
    ]