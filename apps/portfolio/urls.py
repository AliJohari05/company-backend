from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("items/", views.PortfolioListView.as_view(), name="portfolio-list"),
    path(
        "items/<slug:slug>/",
        views.PortfolioDetailView.as_view(),
        name="portfolio-detail",
    ),
]
