from rest_framework import serializers

from account import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = (
            "id",
            "email",
        )


# Application serializers
class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Application
        fields = (
            "ip",
            "name",
            "description",
            "image_url",
            "token",
            "created_on",
        )


class ApplicationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Application
        fields = (
            "ip",
            "name",
            "description",
            "image_url",
            "token",
            "created_on",
        )


# API helper serializers
class APIParentKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return models.Application.objects.filter(
            owner=self.context["request"].user
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ("id", "name")


class EndpointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Endpoint
        fields = ("url", "name", "description", "get_method_display")


# API serializers
class APISerializer(serializers.ModelSerializer):
    class Meta:
        model = models.API
        fields = (
            "id",
            "category",
            "name",
            "short_description",
            "long_description",
            "image",
            "terms_of_use",
            "base_url",
            "is_public",
        )


class APIDetailSerializer(serializers.ModelSerializer):
    endpoints = EndpointsSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = models.API
        fields = (
            "id",
            "category",
            "name",
            "short_description",
            "long_description",
            "image_url",
            "terms_of_use",
            "base_url",
            "endpoints",
            "is_public",
        )


class APIListSerializer(serializers.ModelSerializer):
    endpoints = EndpointsSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    owner = UserSerializer(read_only=True)

    class Meta:
        model = models.API
        fields = (
            "id",
            "owner",
            "category",
            "name",
            "short_description",
            "base_url",
            "image_url",
            "is_public",
            "endpoints",
        )


class APIReadOnlySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = models.API
        fields = (
            "category",
            "name",
            "short_description",
            "long_description",
            "image_url",
            "terms_of_use",
            "base_url",
            "endpoints",
            "is_public",
        )


class APIDetailRetrieveSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source="parent.name")
    category = serializers.CharField(source="category.name")

    class Meta:
        model = models.API
        fields = (
            "id",
            "parent",
            "category",
            "name",
            "short_description",
            "long_description",
            "image_url",
            "terms_of_use",
            "base_url",
            "endpoints",
            "is_public",
        )


# Endpoint serializers
class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Endpoint
        fields = "__all__"


# Token for API
class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
