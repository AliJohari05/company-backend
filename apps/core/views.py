from rest_framework import generics, permissions
from .models import SiteSetting, SocialLink, FAQ
from .serializers import SiteSettingSerializer, SocialLinkSerializer, FAQSerializer


class SiteSettingDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve site general settings, contact info, and social links in a single request.
    """
    serializer_class = SiteSettingSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        setting, _ = SiteSetting.objects.get_or_create(id=1)
        return setting


class SocialLinkListView(generics.ListAPIView):
    """
    GET: List all active social media links.
    """
    queryset = SocialLink.objects.filter(is_active=True)
    serializer_class = SocialLinkSerializer
    permission_classes = [permissions.AllowAny]


class FAQListView(generics.ListAPIView):
    """
    GET: List all active frequently asked questions.
    """
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]