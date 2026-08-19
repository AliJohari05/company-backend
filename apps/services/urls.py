from django.urls import path

from .views import ServiceCategoryListView, ServiceDetailView, ServiceListView

urlpatterns = [
    path("categories/", ServiceCategoryListView.as_view(), name="category_list"),
    path("", ServiceListView.as_view(), name="service_list"),
    path("<slug:slug>/", ServiceDetailView.as_view(), name="service_detail"),
]
