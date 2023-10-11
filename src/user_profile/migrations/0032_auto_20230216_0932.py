from django.db import migrations

from user_profile.country_code import country_json


def insert_country_codes(apps, schema_editor):
    country_code_model = apps.get_model("user_profile", "CountryCode")
    for data in country_json:
        existing_countries = country_code_model.objects.filter(
            country=data["name"]
        ).first()
        if not existing_countries:
            country_code_model.objects.get_or_create(
                country=data["name"], country_code="+" + data["country_code"]
            )
        else:
            existing_countries.country_code = "+" + data["country_code"]
            existing_countries.save()


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0031_alter_countrycode_country"),
    ]

    operations = [
        migrations.RunPython(
            insert_country_codes, reverse_code=migrations.RunPython.noop
        )
    ]
