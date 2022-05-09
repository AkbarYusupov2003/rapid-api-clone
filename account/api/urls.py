from django.urls import path

from . import views

urlpatterns = [

    # Application urls
    path(
        "developer/app-list",
        views.ApplicationListAPIView.as_view(),
        name="app-list",
    ),
    path(
        "developer/app/create",
        views.ApplicationCreateAPIView.as_view(),
        name="app-create",
    ),
    path(
        "developer/app/<int:pk>",
        views.ApplicationDetailAPIView.as_view(),
        name="app-detail",
    ),

    # API urls
    path(
        "developer/app/<int:pk>/api-list",
        views.APIListAPIView.as_view(),
        name="api-list",
    ),
    path(
        "developer/app/<int:pk>/api/create",
        views.APICreateAPIView.as_view(),
        name="api-create",
    ),
    path(
        "developer/app/<int:app_pk>/api/<int:api_pk>",
        views.APIDetailAPIView.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
                "put": "update",
                "patch": "partial_update",
            }
        ),
        name="api-detail",
    ),

    # Endpoint urls
    path(
        "developer/api/<int:pk>/endpoints",
        views.EndpointListCreateAPIView.as_view(),
        name="endpoint-list",
    ),
    path(
        "developer/api/<int:api_pk>/endpoint/<int:endpoint_pk>",
        views.EndpointDetailApiView.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
                "put": "update",
                "patch": "partial_update",
            }
        ),
        name="endpoint-detail",
    ),

    # Users urls
    path(
        "use-api/<int:api_pk>/endpoint/<int:endpoint_pk>",
        views.APIUseGenericAPIView.as_view(),
        name="use-api",
    ),
    path("search/", views.SearchAPIView.as_view(), name="search-list"),
]
