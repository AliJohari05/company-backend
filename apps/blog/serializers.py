from rest_framework import serializers

from .models import Category, Post, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "name_en", "slug", "description", "description_en", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "name_en", "slug", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    tags = serializers.StringRelatedField(many=True)
    excerpt = serializers.CharField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "title_en",
            "slug",
            "excerpt",
            "featured_image",
            "meta_description",
            "meta_description_en",
            "author",
            "category",
            "tags",
            "is_published",
            "published_at",
            "views_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "author", "created_at", "updated_at"]


class PostDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    category_detail = CategorySerializer(source="category", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "title_en",
            "slug",
            "content",
            "content_en",
            "featured_image",
            "meta_description",
            "meta_description_en",
            "author",
            "category",
            "tags",
            "category_detail",
            "tags_detail",
            "is_published",
            "published_at",
            "views_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "author",
            "created_at",
            "updated_at",
            "views_count",
        ]
        extra_kwargs = {
            "category": {"write_only": True, "required": False},
            "tags": {"write_only": True, "required": False},
        }
