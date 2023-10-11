from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from user_profile.models import (
    Analytics,
    Card,
    Connections,
    CountryCode,
    Links,
    ProfileCards,
    Providers,
    UserProfile,
    UserSettings,
    Video,
)
from user_profile.serializers import (
    CardSerializer,
    ConnectionsSerializer,
    CountryCodeSerailizer,
    LinksSerializer,
    ProfileCardsSerializer,
    ProviderObjLinkSerilizer,
    Providerserializer,
    SaveContactSerializer,
    SpecificUserProfileSerializer,
    UserProfileListSerializer,
    UserProfileSerializer,
    UserQRcodeSerializer,
    UserSettingsSerializer,
    VideoSerializer,
)
from user_profile.service import create_profile_cards, get_ip_address


class BaseUserProfileViewset(ModelViewSet):
    def get_queryset(self):
        model_class = self.serializer_class.Meta.model
        profile_id = self.request.GET.get("profile", self.request.data.get("profile"))
        if self.action == "list":
            return model_class.objects.filter(
                profile=profile_id, profile__user=self.request.user
            )
        return model_class.objects.filter(profile__user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        profile_id = self.request.GET.get("profile", self.request.data.get("profile"))
        if not UserProfile.objects.filter(id=profile_id, user=user).exists():
            return Response(
                {"message": "Inavlid Profile"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


class UserProfileViewSet(ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SpecificUserProfileSerializer
        elif self.action == "list":
            return UserProfileListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        return UserProfile.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        existing_profile = UserProfile.objects.filter(user=request.user)
        request_data = request.data
        if not existing_profile:
            request_data["is_active"] = True
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data
        if data.get("is_active") is True or data.get("is_active") == "true":
            UserProfile.objects.filter(user=user, is_active=True).update(
                is_active=False
            )
        instance = serializer.save(user=self.request.user)
        create_profile_cards(instance)

    def perform_update(self, serializer, *args, **kwargs):
        user = self.request.user
        data = self.request.data
        if data.get("is_active") in [True, "true", "True"]:
            UserProfile.objects.filter(user=user, is_active=True).update(
                is_active=False
            )
        serializer.save()

    # check profile name is exists or not
    @action(
        methods=["get"],
        detail=False,
        url_path=r"check-profile-name/(?P<profile_name>[^/.]+)",
        permission_classes=[AllowAny],
    )
    def check_profile_name(self, request, profile_name):
        if profile_name:
            if UserProfile.objects.filter(profile_name=profile_name).exists():
                return Response(
                    {"message": "Already exists"}, status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response({"message": "Available"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "profile_name is required parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # get by profile name
    @action(
        methods=["get"],
        detail=False,
        url_path=r"profile-name/(?P<profile_name>[^/.]+)",
        permission_classes=[AllowAny],
        serializer_class=SpecificUserProfileSerializer,
    )
    def get_profile_by_name(self, request, profile_name):
        if profile_name:
            try:
                data = UserProfile.objects.get(profile_name=profile_name)
                ip = get_ip_address(request)
                profile_views = Analytics.objects.filter(
                    ip_address=ip, profile=data
                ).first()
                if not profile_views and request.user != data.user:
                    Analytics.objects.create(
                        profile=data, analytics_type="profile_views", ip_address=ip
                    )

                serializer = self.get_serializer(data)
                resp = serializer.data
                resp_status = status.HTTP_200_OK
            except Exception as e:
                resp = {}
                resp["message"] = str(e)
                resp_status = status.HTTP_400_BAD_REQUEST
            return Response(resp, resp_status)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"active-user-profile",
        permission_classes=[AllowAny],
        serializer_class=SpecificUserProfileSerializer,
    )
    def get_user_active_profile(self, request, *args, **kargs):
        """
        get active profile
        """
        try:
            queryset = self.get_queryset().get(is_active=True)
            serializer = self.get_serializer(queryset)
            resp = serializer.data
            resp_status = status.HTTP_200_OK
        except Exception as e:
            resp = {}
            resp["message"] = str(e)
            resp_status = status.HTTP_400_BAD_REQUEST
        return Response(resp, resp_status)

    @action(
        methods=["get", "patch"],
        detail=False,
        url_path="profile-cards-postion/(?P<id>[^/.]+)",
        permission_classes=[AllowAny],
        serializer_class=ProfileCardsSerializer,
    )
    def get_profile_card_postion(self, request, id):
        """
        get  profile card for arranging
        """
        profile = UserProfile.objects.get(id=id)
        queryset = ProfileCards.objects.get(profile=profile)
        if request.method == "get":
            try:
                serializer = self.get_serializer(queryset)
                resp = serializer.data
                resp_status = status.HTTP_200_OK
            except Exception as e:
                resp = {}
                resp["message"] = str(e)
                resp_status = status.HTTP_400_BAD_REQUEST
                return Response(resp, resp_status)
        else:
            serializer = self.get_serializer(queryset, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)


class VideoViewSet(BaseUserProfileViewset):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class LinksViewSet(ModelViewSet):
    serializer_class = LinksSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Links.objects.filter(
            is_deleted=False, profile__user=self.request.user
        ).order_by("position")
        return queryset

    @action(
        methods=["post", "get"],
        detail=False,
        url_path="rearrange-links",
        permission_classes=[AllowAny],
    )
    def get_rearrange_links(self, request):
        resp = {}
        link_1 = request.data.get("link1")
        link_2 = request.data.get("link2")
        link_type = request.data.get("link_type")

        if not link_1:
            resp["link1"] = ["This field is required."]

        if not link_2:
            resp["link2"] = ["This field is required."]

        if not link_type:
            resp["link_type"] = ["This field is required."]

        if not link_1 or not link_2:
            return Response(resp, 404)

        try:
            current_user = request.user
            active_profile = UserProfile.objects.filter(
                user=current_user, is_active=True
            ).first()
            link_1 = Links.objects.get(
                id=link_1, types=link_type, profile=active_profile
            )
            link_2 = Links.objects.get(
                id=link_2, types=link_type, profile=active_profile
            )
            if link_1.position > link_2.position:
                queryset = Links.objects.filter(
                    position__gte=link_2.position,
                    position__lt=link_1.position,
                    types=link_type,
                    profile=active_profile,
                ).order_by("position")
                for data in queryset:
                    data.position = data.position + 1
                    data.save()

            if link_1.position < link_2.position:
                queryset = Links.objects.filter(
                    position__lte=link_2.position,
                    position__gt=link_1.position,
                    types=link_type,
                    profile=active_profile,
                ).order_by("position")
                for data in queryset:
                    data.position = data.position - 1
                    data.save()

            link_1.position = link_2.position
            link_1.save()
            result = Links.objects.filter(
                types=link_type, profile=active_profile, is_deleted=False
            )
            serializer = ProviderObjLinkSerilizer(
                result, many=True, context={"request": request}
            )
            return Response(serializer.data, 200)
        except Exception as e:
            resp["message"] = str(e)
            return Response(resp, 404)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.is_deleted:
            resp = {"message": "Invalid link id"}
            status_code = 404
        else:
            instance.is_deleted = True
            instance.save()
            resp = {"message": "Deleted successfully"}
            status_code = 200

        return Response(resp, status_code)


class UserProfileQrViewSet(ModelViewSet):
    serializer_class = UserQRcodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserProfile.objects.filter(user=user, is_active=True)


class ConnectionsViewSet(BaseUserProfileViewset):
    queryset = Connections.objects.all()
    serializer_class = ConnectionsSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        profile = self.request.data.get("profile")
        serializer.save()
        profile_instance = UserProfile.objects.filter(id=profile).first()

        Analytics.objects.create(
            profile=profile_instance,
            analytics_type="exchanged_contacts",
            ip_address=get_ip_address(self.request),
        )

    def create(self, request, *args, **kwargs):
        try:
            return super(BaseUserProfileViewset, self).create(request, *args, **kwargs)
        except Exception as e:
            if "unique contact email" in str(e):
                return Response(
                    {"error": "Connection with this email already exist"}, 404
                )
            elif "unique contact contact number" in str(e):
                return Response(
                    {"error": "Connection with this contact number already exist"}, 404
                )
            else:
                raise e


class CountryCodeViewSet(ReadOnlyModelViewSet):
    queryset = CountryCode.objects.all()
    serializer_class = CountryCodeSerailizer
    # permission_classes = [IsAuthenticated]


class ProvidersViewset(ReadOnlyModelViewSet):
    queryset = Providers.objects.all()
    serializer_class = Providerserializer
    permission_classes = [IsAuthenticated]


class AnalyticsEventViewSet(APIView):
    serializer_class = SaveContactSerializer

    def post(self, request, *args, **kwargs):
        event = request.data.get("event")
        profile = request.data.get("profile")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile_instance = UserProfile.objects.filter(id=profile).first()
        if profile_instance:
            if event == "save_contact":
                Analytics.objects.create(
                    profile=profile_instance,
                    analytics_type="saved_contacts",
                    ip_address=get_ip_address(request),
                )
                return Response(
                    {"message": "Contact Saved"}, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"message": "Inavlid Event"}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"message": "Invalid Profile ID"}, status=status.HTTP_404_NOT_FOUND
            )


class UserSettingsViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        model_class = self.serializer_class.Meta.model
        return model_class.objects.filter(user=self.request.user)


class CardsViewSet(ReadOnlyModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [AllowAny]
    queryset = Card.objects.filter(Q(printed=True) | Q(assigned=True))

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SpecificUserProfileSerializer
        return super().get_serializer_class()

    def retrieve(
        self,
        request,
        *args,
        **kwargs,
    ):
        instance = self.get_object()
        if instance.user:
            user_profile = UserProfile.objects.filter(
                user=instance.user.id, is_active=True
            ).first()
            if user_profile:
                ip = get_ip_address(request)
                profile_views = Analytics.objects.filter(
                    ip_address=ip, profile=user_profile
                ).first()
                if not profile_views:
                    Analytics.objects.create(
                        profile=user_profile,
                        analytics_type="profile_views",
                        ip_address=ip,
                    )

                serializer = self.get_serializer(user_profile)
                return Response(serializer.data)
            else:
                return Response({"message": "No profile found"}, 204)
        return Response({"message": "No user associated with this card"}, 403)
