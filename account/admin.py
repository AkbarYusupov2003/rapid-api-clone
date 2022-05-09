from django.contrib import admin

from .models import API, Application, Category, Endpoint, User


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    search_fields = ("owner__email", "name")
    fields = (
        "owner",
        "name",
        "ip",
        "image",
        "requests_limit",
        "description",
        "token",
    )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.readonly_fields = ("created_on",)
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    filter_horizontal = ("endpoints",)


admin.site.register(User)
admin.site.register(Category)
admin.site.register(Endpoint)
