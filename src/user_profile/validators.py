ifrom django.core.validators import URLValidator
from django.core.validators import validate_email as ve
from rest_framework import serializers


class PhoneSerializer(serializers.Serializer):
    phone_type = serializers.CharField(max_length=15)
    country_code = serializers.IntegerField()
    contact_number = serializers.RegexField(
        r"^\+?1?\d{8,15}$", max_length=16, min_length=7
    )


class AddressSerializer(serializers.Serializer):
    address_type = serializers.CharField(max_length=100)
    street_line_one = serializers.CharField(max_length=300)
    street_line_two = serializers.CharField(
        allow_null=True, required=False, allow_blank=True
    )
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.IntegerField()
    country = serializers.CharField(max_length=50)


def validate_phone(value):
    PhoneSerializer(data=value, many=True).is_valid(raise_exception=True)


def validate_email(value):
    [ve(i) for i in value]


def validate_website(value):
    [URLValidator(i) for i in value]


def validate_address(value):
    AddressSerializer(data=value, many=True).is_valid(raise_exception=True)
