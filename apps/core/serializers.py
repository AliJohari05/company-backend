from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import ContactMessage, FAQ, SiteSetting, SocialLink


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ("id", "title", "url", "icon")


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "question_en", "answer_en", "order")


class SiteSettingSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = ContactMessage
        fields = ("id", "name", "email", "phone_number", "subject", "message", "created_at")
        read_only_fields = ("id", "created_at")
