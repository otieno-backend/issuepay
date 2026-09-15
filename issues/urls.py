from django.urls import path

from .views import IssueDetailView, IssueListCreateView


urlpatterns = [
    path("", IssueListCreateView.as_view(), name="issue-list-create"),
    path("<int:pk>/", IssueDetailView.as_view(), name="issue-detail"),
]
