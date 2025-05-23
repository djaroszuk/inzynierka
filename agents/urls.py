from django.urls import path
from .views import (
    AgentListView,
    AgentCreateView,
    AgentDetailView,
    AgentUpdateView,
    AgentDeleteView,
    AgentStatsView,
    AllAgentsStatsView,
    SendEmailView,
)


app_name = "agents"

urlpatterns = [
    path("", AgentListView.as_view(), name="agent-list"),
    path("create/", AgentCreateView.as_view(), name="agent-create"),
    path("all/stats", AllAgentsStatsView.as_view(), name="all-agents-statistics"),
    path("<int:pk>/", AgentDetailView.as_view(), name="agent-detail"),
    path("<int:pk>/update/", AgentUpdateView.as_view(), name="agent-update"),
    path("<int:pk>/delete/", AgentDeleteView.as_view(), name="agent-delete"),
    path("<int:pk>/stats/", AgentStatsView.as_view(), name="agent-stats"),
    path("send-email", SendEmailView.as_view(), name="send-email"),
]
