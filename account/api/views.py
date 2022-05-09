import requests
from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, viewsets
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from account.models import API, Application, Endpoint

from . import serializers


# Application Views
class PaginationByTen(PageNumberPagination):
    page_size = 10
    page_query_param = "page_size"
    max_page_size = 20


class ApplicationListAPIView(generics.ListAPIView):
    queryset = Application.objects.all()
    serializer_class = serializers.ApplicationSerializer
    pagination_class = PaginationByTen

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)


class ApplicationCreateAPIView(generics.CreateAPIView):
    queryset = Application.objects.all()
    serializer_class = serializers.ApplicationSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ApplicationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Application.objects.all()
    serializer_class = serializers.ApplicationDetailSerializer

    def get_object(self):
        if self.queryset.filter(pk=self.kwargs["pk"], owner=self.request.user):
            return super().get_object()
        raise NotFound(detail="Not found.", code=404)

    def get(self, request, *args, **kwargs):
        app_instance = self.get_object()
        connected_apis = API.objects.filter(
            parent__pk=self.kwargs["pk"], owner=self.request.user
        )
        app_serializer = self.get_serializer(app_instance)
        connected_apis_serializer = serializers.APIReadOnlySerializer(
            connected_apis, many=True
        )
        return Response(
            {
                "Application": app_serializer.data,
                "Connected APIs": connected_apis_serializer.data,
            },
            status=200,
        )


# API views
class APIListAPIView(generics.ListAPIView):
    serializer_class = serializers.APIListSerializer
    pagination_class = PaginationByTen

    def get_queryset(self):
        app = get_object_or_404(
            Application.objects.prefetch_related("apis"), pk=self.kwargs["pk"]
        )
        return (
            app.apis.all()
            .select_related(
                "category",
            )
            .prefetch_related("endpoints")
        )


class APICreateAPIView(generics.CreateAPIView):
    queryset = API.objects.select_related("category")
    serializer_class = serializers.APISerializer

    def perform_create(self, serializer):
        parent = get_object_or_404(
            Application, pk=self.kwargs["pk"], owner=self.request.user
        )
        serializer.save(parent=parent, owner=self.request.user)


class APIDetailAPIView(viewsets.ModelViewSet):
    serializer_class = serializers.APISerializer

    def get_object(self):
        app = get_object_or_404(
            Application.objects.prefetch_related("apis"),
            pk=self.kwargs["app_pk"],
            owner=self.request.user,
        )
        api = get_object_or_404(
            app.apis.all()
            .select_related("category")
            .prefetch_related("endpoints"),
            pk=self.kwargs["api_pk"],
            owner=self.request.user,
        )
        return api

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.APIDetailSerializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        api = get_object_or_404(
            API, pk=self.kwargs["api_pk"], owner=self.request.user
        )
        response = serializers.APIDetailSerializer(api)
        return Response(response.data)


# Endpoints views
class EndpointListCreateAPIView(generics.ListCreateAPIView):
    queryset = Endpoint.objects.all()
    serializer_class = serializers.EndpointSerializer
    pagination_class = PaginationByTen

    def get_queryset(self):
        api = get_object_or_404(
            API.objects.prefetch_related("endpoints"),
            pk=self.kwargs["pk"],
            owner=self.request.user,
        )
        return api.endpoints.all()

    def post(self, request, *args, **kwargs):
        created_instance = self.create(request, *args, **kwargs)
        api = get_object_or_404(
            API.objects.prefetch_related("endpoints"), pk=self.kwargs["pk"]
        )
        api.endpoints.add(
            self.queryset.filter(id=created_instance.data["id"]).first()
        )
        api.save()
        return created_instance


class EndpointDetailApiView(viewsets.ModelViewSet):
    queryset = Endpoint.objects.all()
    serializer_class = serializers.EndpointSerializer

    def get_object(self):
        api = get_object_or_404(
            API.objects.prefetch_related("endpoints"), pk=self.kwargs["api_pk"]
        )
        endpoint = get_object_or_404(
            api.endpoints.all(), pk=self.kwargs["endpoint_pk"]
        )
        return endpoint


# send token and get API's response
class APIUseGenericAPIView(generics.GenericAPIView):
    """
    Pass token in post request
    """

    queryset = API.objects.all()
    serializer_class = serializers.TokenSerializer

    def post(self, request, *args, **kwargs):

        api = get_object_or_404(
            self.queryset.select_related("parent"), pk=self.kwargs["api_pk"]
        )

        if api.parent.token == self.request.POST["token"]:

            endpoint = get_object_or_404(
                Endpoint, pk=self.kwargs["endpoint_pk"]
            )
            url = f"{api.base_url}{endpoint.url}"
            method = endpoint.get_method_display()
            headers = {
                "User-Agent": "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64; rv:99.0) "
                "Gecko/20100101 Firefox/99.0"
            }
            try:
                response = requests.request(method, url, headers=headers)
            except:
                raise NotFound(
                    detail="Not found.Validate your url and method type.",
                    code=404,
                )

            json = response.json()
            if json:
                # ↓ Checking User request limit ↓
                if self.request.user.requests_limit == 0:
                    raise NotAcceptable(
                        detail="The limit of your requests has been reached.",
                        code=406,
                    )
                elif self.request.user.requests_limit != -1:
                    request.user.requests_limit = F("requests_limit") - 1
                    request.user.save()
                # ↓ Checking Application request limit ↓
                if api.parent.requests_limit == 0:
                    raise NotAcceptable(
                        detail="The limit of requests to applications has been reached.",
                        code=406,
                    )
                elif api.parent.requests_limit != -1:
                    api.parent.requests_limit = F("requests_limit") - 1
                    api.parent.save()
                return Response(json, status=200)

        raise NotFound(detail="Not found.", code=404)


class SearchAPIView(generics.ListAPIView):
    queryset = API.objects.all()
    serializer_class = serializers.APIListSerializer
    permission_classes = (permissions.AllowAny,)
    filterset_fields = ("category",)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("name",)
