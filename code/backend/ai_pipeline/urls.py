from django.db import transaction
from django.urls import path

from .views import AnalysisView, RequestDetailView, RequestListView, RunDetailView

urlpatterns = [
    path("reports/<uuid:report_id>/analyses/", transaction.non_atomic_requests(AnalysisView.as_view())),
    path("reports/<uuid:report_id>/analysis-runs/<uuid:run_id>/", RunDetailView.as_view()),
    path("requests/", RequestListView.as_view()),
    path("requests/<uuid:key>/", RequestDetailView.as_view()),
]
