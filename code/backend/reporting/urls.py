from django.urls import path
from .views import ReportListCreate, ReportDetail, EvidenceListUpload, BundleCreateView, EvidenceMedia
from .review_views import (CardRevisionView, HistoryView, NarrativeRevisionView, NotificationListView,
                           NotificationReadView, SubmitView, VerificationView, VersionDetailView, VersionListView)

urlpatterns = [
    path('reports/', ReportListCreate.as_view(), name='slr10-reports'),
    path('reports/<uuid:pk>/', ReportDetail.as_view(), name='slr10-report-detail'),
    path('reports/<uuid:pk>/evidence/', EvidenceListUpload.as_view(), name='slr10-evidence'),
    path('reports/<uuid:pk>/bundles/', BundleCreateView.as_view(), name='slr10-bundle'),
    path('evidence/<uuid:pk>/media/', EvidenceMedia.as_view(), name='slr10-media'),
    path('reports/<uuid:pk>/narratives/revisions/', NarrativeRevisionView.as_view(), name='slr12-narrative-revision'),
    path('reports/<uuid:pk>/cards/revisions/', CardRevisionView.as_view(), name='slr12-card-revision'),
    path('reports/<uuid:pk>/human-verifications/', VerificationView.as_view(), name='slr12-verification'),
    path('reports/<uuid:pk>/submit/', SubmitView.as_view(), name='slr12-submit'),
    path('reports/<uuid:pk>/versions/', VersionListView.as_view(), name='slr12-versions'),
    path('reports/<uuid:pk>/versions/<str:kind>/<uuid:version_id>/', VersionDetailView.as_view(), name='slr12-version-detail'),
    path('reports/<uuid:pk>/history/', HistoryView.as_view(), name='slr12-history'),
    path('notifications/', NotificationListView.as_view(), name='slr12-notifications'),
    path('notifications/<uuid:pk>/read/', NotificationReadView.as_view(), name='slr12-notification-read'),
]
