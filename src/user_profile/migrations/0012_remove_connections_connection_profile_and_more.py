# Generated by Django 4.1.3 on 2022-12-19 10:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0011_rename_user_profile_id_analytics_profile_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="connections",
            name="connection_profile",
        ),
        migrations.AddField(
            model_name="connections",
            name="contact_number",
            field=models.CharField(default=1, max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="connections",
            name="email",
            field=models.EmailField(
                default="2022-12-12 17:23:00.117 +0530", max_length=254
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="connections",
            name="name",
            field=models.CharField(default="2022-12-12", max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="connections",
            name="profile",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="user_profile.userprofile",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="bio_details",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="profile_picture",
            field=models.ImageField(upload_to="profile"),
        ),
        migrations.DeleteModel(
            name="SharedDetails",
        ),
    ]