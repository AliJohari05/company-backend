from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.StringRelatedField(source="user", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "user", "user_name", "post", "service", "parent", "content", "rating", "is_approved", "created_at", "replies")
        read_only_fields = ("id", "user", "user_name", "is_approved", "created_at", "replies")

    def get_replies(self, obj):
        return ReviewSerializer(obj.replies.filter(is_approved=True), many=True, context=self.context).data

    def validate(self, attrs):
        parent = attrs.get("parent")
        post, service = attrs.get("post"), attrs.get("service")
        if parent and post is None and service is None:
            attrs["post"], attrs["service"] = parent.post, parent.service
            post, service = attrs["post"], attrs["service"]
        if (post is None) == (service is None):
            raise serializers.ValidationError("Set exactly one of post or service.")
        if parent and (parent.post_id != getattr(post, "id", None) or parent.service_id != getattr(service, "id", None)):
            raise serializers.ValidationError("Reply must belong to the same target.")
        return attrs

    def create(self, validated_data):
        return Review.objects.create(user=self.context["request"].user, **validated_data)
