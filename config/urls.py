import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .yasg import urlpatterns as doc_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("account.api.urls")),
]

urlpatterns += doc_urls

if settings.DEBUG:
    urlpatterns.append(path("__debug__", include(debug_toolbar.urls))),
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
