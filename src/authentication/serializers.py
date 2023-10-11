from difflib import SequenceMatcher

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from authentication.models import InvitationCode


def generate_otp(length=4, allowed_chars="0123456789"):
    return str(get_random_string(length, allowed_chars=allowed_chars))


class ResetPAsswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
    )

    def validate(self, attrs):
        request = self.context.get("request")
        email = request.user.username
        password = attrs.get("new_password")

        # Validate password length
        validate_password(password)

        # Validate password similarity to username
        username = email.split("@")[0]
        similarity = SequenceMatcher(None, username, password).ratio()
        if similarity >= 0.5:
            raise serializers.ValidationError(
                {"password": "Password is too similar to username"}
            )

        return attrs


# Serializer to Register User
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        required=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "password",
            "email",
            "first_name",
            "last_name",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["email"],
            password=validated_data["password"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class InvitationCodeSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    password = serializers.CharField(read_only=True)

    class Meta:
        model = InvitationCode
        fields = ("email", "first_name", "password")

    def create(self, validated_data):
        invitation_code = InvitationCode.objects.filter(
            email=validated_data["email"],
            is_used=False,
        ).first()
        if invitation_code:
            invitation_code.first_name = validated_data["first_name"]
        else:
            invitation_code = super().create(validated_data)
        invitation_code.code = generate_otp()
        invitation_code.save()
        return invitation_code

    def validate(self, attrs):
        email = attrs.get("email")
        request = self.context["request"]
        password = request.data.get("password")
        first_name = attrs.get("first_name")

        # Validate password length
        validate_password(password)

        # Validate password similarity to username
        email = email.split("@")[0]
        username = first_name
        email_similarity = SequenceMatcher(None, email, password).ratio()
        if email_similarity >= 0.5:
            raise serializers.ValidationError(
                {"password": "Password is too similar to email"}
            )

        username_similarity = SequenceMatcher(None, username, password).ratio()
        if username_similarity >= 0.5:
            raise serializers.ValidationError(
                {"password": "Password is too similar to username"}
            )
        return attrs
