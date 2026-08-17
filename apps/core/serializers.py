from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import SiteSetting, SocialLink, FAQ


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ('id', 'title', 'url', 'icon')


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer', 'order')


class SiteSettingSerializer(serializers.ModelSerializer):
    social_links = serializers.SerializerMethodField()

    class Meta:
        model = SiteSetting
        fields = (
            'site_name',
            'site_logo',
            'about_us',
            'email',
            'phone_number',
            'address',
            'working_hours',
            'social_links'
        )

    @extend_schema_field(SocialLinkSerializer(many=True))
    def get_social_links(self, obj):
        active_links = SocialLink.objects.filter(is_active=True)
        return SocialLinkSerializer(active_links, many=True).data
