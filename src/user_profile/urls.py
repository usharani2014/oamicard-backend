from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user_profile.views import (
    AnalyticsEventViewSet,
    CardsViewSet,
    ConnectionsViewSet,
    CountryCodeViewSet,
    LinksViewSet,
    ProvidersViewset,
    UserProfileQrViewSet,
    UserProfileViewSet,
    UserSettingsViewSet,
    VideoViewSet,
)

router = DefaultRouter()
router.register("user", UserProfileViewSet, basename="snippet")
router.register("video", VideoViewSet, basename="video")
router.register("links", LinksViewSet, basename="links")
router.register("qr-code", UserProfileQrViewSet, basename="qr-code")
router.register("connections", ConnectionsViewSet, basename="connections")
router.register("user-settings", UserSettingsViewSet, basename="user-settings")
router.register("card", CardsViewSet, basename="card")


urlpatterns = [
    path(r"", include(router.urls)),
    path("country-code/", CountryCodeViewSet.as_view({"get": "list"})),
    path("providers/", ProvidersViewset.as_view({"get": "list"})),
    path("contact-save/", AnalyticsEventViewSet.as_view()),
]
