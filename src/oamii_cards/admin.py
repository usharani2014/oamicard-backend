from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export import fields, resources
from import_export.admin import (  # ExportForm,; ExportMixin,
    ExportActionMixin,
    ImportExportFormBase,
)

from user_profile.models import Card
from user_profile.service import create_qr_code

apps_to_register = ["user_profile", "authentication"]
models = [model for app in apps_to_register for model in apps.all_models[app].values()]
for model in models:
    try:
        admclass = type(
            model._meta.model.__name__ + "Admin",
            (admin.ModelAdmin,),
            {"list_display": tuple(map(lambda obj: obj.name, model._meta.fields))},
        )
        if model.__name__ != "Card":
            admin.site.register(model, admclass)

    except admin.sites.AlreadyRegistered:
        pass
    except Exception as msg:
        print(msg)


class CardResource(resources.ModelResource):
    card_number = fields.Field(attribute="card_number", column_name="card_number")
    card = fields.Field(attribute="card", column_name="card")
    card_link = fields.Field(attribute="card_link", column_name="card_link")

    class Meta:
        model = Card
        fields = ("card_number", "card", "card_link")


class CardListFilter(admin.SimpleListFilter):
    title = "card"

    parameter_name = "decade"

    def lookups(self, request, model_admin):
        return (
            ("used", _("Used cards")),
            ("unused", _("Unused cards")),
            ("printed", _("Printed cards")),
        )

    def queryset(self, request, queryset):
        if self.value() == "used":
            return queryset.exclude(user=None)
        if self.value() == "unused":
            return queryset.filter(printed=False, assigned=False)
        if self.value() == "printed":
            return queryset.filter(printed=True)


class NewExportForm(ImportExportFormBase):
    file_format = forms.ChoiceField(
        label=_("Format"),
        choices=(),
    )
    printed = forms.BooleanField(
        label=_("printed"),
        required=False,
    )

    def __init__(self, formats, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for i, f in enumerate(formats):
            choices.append(
                (
                    str(i),
                    f().get_title(),
                )
            )
        if len(formats) > 1:
            choices.insert(0, ("", "---"))

        self.fields["file_format"].choices = choices
        self.fields["printed"].initial = False


class CardForm(forms.ModelForm):
    no_of_cards = forms.IntegerField(required=True)
    label = forms.CharField(required=True)
    printed = forms.BooleanField()

    class Meta:
        model = Card
        fields = ("no_of_cards", "label", "printed")


class CardAdmin(ExportActionMixin, admin.ModelAdmin):
    list_max_show_all = 20000000
    list_display = (
        "card_serial_no",
        "card",
        "card_link",
        "card_qr_code",
        "user",
        "printed",
        "assigned",
        "label",
    )
    list_filter = (CardListFilter, "label")
    resource_classes = [CardResource]
    export_form_class = NewExportForm
    ordering = ["-card_serial_no"]
    actions = [
        "mark_as_printed",
        "mark_as_assigned",
        "mark_as_unprinted",
        "mark_as_unassigned",
    ]

    def mark_as_printed(self, request, queryset):
        queryset.update(printed=True)

    def mark_as_assigned(self, request, queryset):
        queryset.update(assigned=True)

    def mark_as_unprinted(self, request, queryset):
        queryset.update(printed=False)

    def mark_as_unassigned(self, request, queryset):
        queryset.update(assigned=False)

    mark_as_assigned.short_description = "Mark As Assigned"
    mark_as_printed.short_description = "Mark As Printed"
    mark_as_unprinted.short_description = "Remove Printed Label"
    mark_as_unassigned.short_description = "Remove Assigned Label"

    def get_queryset(self, request):
        qs = super(CardAdmin, self).get_queryset(request)
        qs = qs.filter(is_deleted=False).order_by("card_serial_no")
        return qs

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}

        extra_context["show_save_and_continue"] = False

        return super().changeform_view(request, object_id, form_url, extra_context)

    def card_qr_code(self, obj):
        base64_image = create_qr_code(obj.card_link, box_size=3)
        return format_html(
            '<img src="data:image/png;base64, {}"/>', base64_image.decode()
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is None and change is False:
            form = CardForm
            form.base_fields["no_of_cards"] = forms.IntegerField()
            form.base_fields["printed"] = forms.BooleanField(required=False)
            return form
        else:
            form = forms.modelform_factory(
                self.model,
                exclude=("is_deleted",),
            )
            return form

    def save_model(self, request, obj, form, change, **kwargs):
        """
        Given a model instance save it to the database.
        """
        if change is False:
            from_data = form.data
            total_count = Card.objects.all()
            if total_count:
                total_count = total_count.order_by("-card_serial_no")[0]
                total = total_count.card_serial_no
            else:
                total = 0
            cards = from_data.get("no_of_cards")
            batch = from_data.get("label")
            printed = from_data.get("printed")
            if cards and batch:
                card_obj = [
                    Card(
                        user_id=None,
                        card_serial_no=total + i,
                        label=batch,
                        printed=True if printed else False,
                    )
                    for i in range(1, int(cards) + 1)
                ]
                Card.objects.bulk_create(card_obj)
                if obj.card_serial_no:
                    obj.save()
        else:
            obj.save()
            return super().get_form(request, obj, change, **kwargs)

    # def export_action(self, request, *args, **kwargs):
    #     data = request.POST
    #     if "printed" == request.GET.get("decade"):
    #         self.export_form_class = ExportForm
    #     else:
    #         self.export_form_class = NewExportForm
    #     if "printed" in data.keys():
    #         queryset = self.get_export_queryset(request)
    #         queryset.update(printed=True)
    #     return super().export_action(request, *args, **kwargs)

    def delete_queryset(self, request, queryset) -> None:
        # from action queryset
        """
        Given a queryset, delete it from the database.
        """
        for data in queryset:
            if data.user:
                username = data.user
                data.user = None
                User.objects.filter(username=username).delete()
            data.is_deleted = True
            data.save()

    def delete_model(self, request, obj):
        """
        Given a model instance delete it from the database.
        """
        # form selected object
        user = obj.user
        if obj.user:
            obj.user = None
            User.objects.filter(username=user).delete()
        obj.is_deleted = True
        obj.save()


admin.site.register(Card, CardAdmin)
