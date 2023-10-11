from django.contrib import admin

from authentication.models import InvitationCode, Request


class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "code", "is_used")


admin.site.register(InvitationCode, InvitationCodeAdmin)


class RequestAdmin(admin.ModelAdmin):
    list_display = ("endpoint", "created_at")


admin.site.register(Request, RequestAdmin)
