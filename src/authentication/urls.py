from django.urls import include, path
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter

from authentication.views import (
    ResetPasswordViewSet,
    SendInviationCodeViewSet,
    UserViewSet,
)

resetpassword = ResetPasswordViewSet.as_view({"put": "update"})

router = DefaultRouter()
router.register("user", UserViewSet, basename="user")

urlpatterns = [
    path("api-token/", views.obtain_auth_token),
    path("reset-password/", resetpassword, name="reset-password"),
    path(r"", include(router.urls)),
    path(
        "forget-password/",
        include("django_rest_passwordreset.urls", namespace="forget-password"),
    ),
    path("invitation-code/", SendInviationCodeViewSet.as_view({"post": "create"})),
]
