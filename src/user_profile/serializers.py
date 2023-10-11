from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q
from rest_framework import serializers

from user_profile.models import (
    Analytics,
    Card,
    Connections,
    CountryCode,
    Links,
    ProfileCards,
    Providers,
    User,
    UserProfile,
    UserSettings,
    Video,
)
from user_profile.service import create_asset_qr


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class Providerserializer(serializers.ModelSerializer):
    class Meta:
        model = Providers
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = UserProfile
        fields = "__all__"


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = "__all__"


class LinksSerializer(serializers.ModelSerializer):
    position = serializers.IntegerField(read_only=True)

    class Meta:
        model = Links
        fields = "__all__"

    def validate(self, attrs):
        if attrs["types"] != "website" and attrs.get("provider") is None:
            raise serializers.ValidationError("Provider is required for this type.")
        request = self.context.get("request")
        user = request.user
        if attrs["profile"].user != user:
            raise serializers.ValidationError("Invalid profile ID")
        return super().validate(attrs)

    def create(self, validated_data):
        # Set default values for fields
        position = Links.objects.filter(
            profile=validated_data["profile"],
            types=validated_data["types"],
        ).count()
        validated_data["position"] = validated_data.get("position", position + 1)
        # Call the superclass's create method to perform the actual object creation
        return super(LinksSerializer, self).create(validated_data)


class UserQRcodeSerializer(serializers.Serializer):
    qr_code = serializers.SerializerMethodField("get_qr_data")

    def get_qr_data(self, obj: User):
        return create_asset_qr(obj)


class ConnectionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connections
        fields = "__all__"


class CountryCodeSerailizer(serializers.ModelSerializer):
    class Meta:
        model = CountryCode
        fields = "__all__"


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = "__all__"


class ProviderObjLinkSerilizer(LinksSerializer):
    provider = Providerserializer(read_only=True)


class SpecificUserProfileSerializer(UserProfileSerializer):
    links_set = serializers.SerializerMethodField("get_links_set")
    video = VideoSerializer(read_only=True)
    analytics_set = serializers.SerializerMethodField()
    settings = serializers.SerializerMethodField("get_user_settings")
    user = serializers.SerializerMethodField("get_user_detail")

    def get_links_set(self, obj):
        request = self.context.get("request")
        result = Links.objects.filter(profile__id=obj.id, is_deleted=False)
        return ProviderObjLinkSerilizer(
            result, many=True, context={"request": request}
        ).data

    def get_user_settings(self, obj):
        results = UserSettings.objects.filter(user=obj.user.id).first()
        return UserSettingsSerializer(results).data

    def get_user_detail(self, obj):
        results = User.objects.filter(id=obj.user.id).first()
        return UserSerializer(results).data

    def get_analytics_set(self, obj):
        current_date = date.today()
        one_month = current_date - relativedelta(months=1)
        six_months = current_date - relativedelta(months=6)
        one_year = current_date - relativedelta(years=1)
        two_year = current_date - relativedelta(years=2)
        data = {}
        if Analytics.objects.filter(profile__id=obj.id).exists():
            data = (
                Analytics.objects.filter(profile__id=obj.id)
                .values("analytics_type")
                .annotate(
                    total_count=Count("analytics_type"),
                    one_month_count=Count(
                        "created_at",
                        filter=(Q(created_at__gte=one_month)),
                    ),
                    six_month_count=Count(
                        "created_at",
                        filter=(Q(created_at__gte=six_months)),
                    ),
                    one_year_count=Count(
                        "created_at",
                        filter=(Q(created_at__gte=one_year)),
                    ),
                    two_year_count=Count(
                        "created_at",
                        filter=(Q(created_at__gte=two_year)),
                    ),
                )
            )
        resp = {}

        if data:
            for entry in data:
                name = entry.pop("analytics_type")
                resp[name] = entry

        data_dict = {
            "total_count": 0,
            "one_month_count": 0,
            "six_month_count": 0,
            "one_year_count": 0,
            "two_year_count": 0,
        }
        if "profile_views" not in resp:
            resp["profile_views"] = data_dict
        if "saved_contacts" not in resp:
            resp["saved_contacts"] = data_dict
        if "exchanged_contacts" not in resp:
            resp["exchanged_contacts"] = data_dict

        return resp


class SaveContactSerializer(serializers.Serializer):
    event = serializers.CharField(required=True)
    profile = serializers.UUIDField(required=True)


class UserProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "id",
            "profile_name",
            "is_active",
            "profile_picture",
            "first_name",
            "last_name",
            "company_name",
            "position",
        ]


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = "__all__"


class ProfileCardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileCards
        fields = "__all__"


class PositionLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Links
        fields = "__all__"
