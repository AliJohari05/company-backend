from django.urls import path
from .views import (
    TicketListCreateView,
    TicketDetailView,
    TicketMessageCreateView,
    TicketCloseView,
)

app_name = 'tickets'

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('<int:ticket_id>/messages/', TicketMessageCreateView.as_view(), name='ticket-message-create'),
    path('<int:pk>/close/', TicketCloseView.as_view(), name='ticket-close'),
]