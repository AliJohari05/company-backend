from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Review


class AdminReplySerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000)


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.StringRelatedField(source="user", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "user", "user_name", "post", "service", "parent", "content", "rating", "is_approved", "created_at", "replies")
        read_only_fields = ("id", "user", "user_name", "is_approved", "created_at", "replies")

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_replies(self, obj):
        return ReviewSerializer(obj.replies.filter(is_approved=True), many=True, context=self.context).data

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        post = attrs.get("post", getattr(self.instance, "post", None))
        service = attrs.get("service", getattr(self.instance, "service", None))
        if parent and post is None and service is None:
            attrs["post"], attrs["service"] = parent.post, parent.service
            post, service = attrs["post"], attrs["service"]
        if (post is None) == (service is None):
            raise serializers.ValidationError("Set exactly one of post or service.")
        if parent and (parent.post_id != getattr(post, "id", None) or parent.service_id != getattr(service, "id", None)):
            raise serializers.ValidationError("Reply must belong to the same target.")
        if parent and parent.parent_id:
            raise serializers.ValidationError("Replies cannot be nested more than one level.")
        if parent and attrs.get("rating") is not None:
            raise serializers.ValidationError({"rating": "Replies cannot include a rating."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Review.objects.create(
            user=request.user,
            is_approved=request.user.is_staff,
            **validated_data,
        )
