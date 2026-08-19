from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path(
        'private-files/<path:file_path>',
        views.PrivateMediaFileDownloadView.as_view(),
        name='private-file-download',
    ),
    path('settings/', views.SiteSettingDetailView.as_view(), name='site-settings'),
    path('social-links/', views.SocialLinkListView.as_view(), name='social-links-list'),
    path('faqs/', views.FAQListView.as_view(), name='faq-list'),
]
