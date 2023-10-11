from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentication.models import InvitationCode
from authentication.serializers import (
    InvitationCodeSerializer,
    RegisterSerializer,
    ResetPAsswordSerializer,
    UserSerializer,
)
from user_profile.models import Card


def generate_otp(length=4, allowed_chars="0123456789"):
    """Generates a random otp for given length"""
    return get_random_string(length, allowed_chars=allowed_chars)


def check_card(card):
    if (
        Card.objects.filter(card=card, user=None)
        .filter(Q(printed=True) | Q(assigned=True))
        .exists()
    ):
        return True


class ResetPasswordViewSet(ModelViewSet):
    serializer_class = ResetPAsswordSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Check old password
        if not instance.check_password(serializer.data.get("old_password")):
            return Response(
                {"old_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # set_password also hashes the password that the user will get
        instance.set_password(serializer.data.get("new_password"))
        instance.save()
        response = {
            "status": "success",
            "code": status.HTTP_200_OK,
            "message": "Password updated successfully",
            # 'data': []
        }

        return Response(response)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[AllowAny],
        serializer_class=RegisterSerializer,
    )
    def register(self, request, *args, **kwargs):
        # This logic was taken from the `create` on `ModelViewSet`. Alter as needed.
        card = request.data.get("card")
        invitation_code = request.data.get("invitation_code")
        resp = {}
        if card:
            card_data = check_card(card)

            if card_data:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                otp = InvitationCode.objects.filter(
                    is_used=False,
                    code=invitation_code,
                    email=request.data.get("email"),
                ).update(is_used=True)
                if otp:
                    serializer.save()
                    data = serializer.data
                    user = data.get("id")
                    Card.objects.filter(card=card).update(user=user, assigned=True)
                    resp = serializer.data
                else:
                    resp["message"] = "Inavlid otp"
                    return Response(resp, 401)
            else:
                resp["message"] = "Card does not exists"
                return Response(resp, 400)
        else:

            resp["message"] = "Card Id is required"
            return Response(resp, 400)
        return Response(resp)


class SendInviationCodeViewSet(ModelViewSet):
    serializer_class = InvitationCodeSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        request_data = request.data
        card_id = request_data.get("card")
        if not request_data.get("card"):
            return Response({"card": ["This field is required"]}, 400)

        if not request_data.get("password"):
            return Response({"password": ["This field is required"]}, 400)

        # check card
        card = check_card(card_id)
        if card:
            serializer = self.get_serializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            existing_email = User.objects.filter(email=request_data["email"]).exists()
            if existing_email:
                return Response({"message": "Email Already Registered"}, 400)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        return Response({"message": "Invalid card"}, 400)
