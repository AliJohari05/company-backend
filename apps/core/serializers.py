from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import ContactMessage, FAQ, SiteSetting, SocialLink
from .localization import LocalizedContentSerializerMixin


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ("id", "title", "url", "icon")


class FAQSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("question", "answer")
    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "question_en", "answer_en", "order")


class SiteSettingSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("site_name", "about_us", "address", "working_hours")
    social_links = serializers.SerializerMethodField()

    class Meta:
        model = SiteSetting
        fields = (
            "site_name",
            "site_name_en",
            "site_logo",
            "about_us",
            "about_us_en",
            "email",
            "phone_number",
            "address",
            "address_en",
            "working_hours",
            "working_hours_en",
            "social_links",
        )

    @extend_schema_field(SocialLinkSerializer(many=True))
    def get_social_links(self, obj):
        active_links = SocialLink.objects.filter(is_active=True)
        return SocialLinkSerializer(active_links, many=True).data


class ContactMessageSerializer(serializers.ModelSerializer):
    website = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    class Meta:
        model = ContactMessage
        fields = ("id", "name", "email", "phone_number", "subject", "message", "website", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_website(self, value):
        if value:
            raise serializers.ValidationError("Invalid form submission.")
        return value

    def create(self, validated_data):
        validated_data.pop("website", None)
        return super().create(validated_data)
