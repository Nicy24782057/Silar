from django.urls import path
from .views import ReportListCreate, ReportDetail, EvidenceListUpload, BundleCreateView, EvidenceMedia

urlpatterns = [
    path('reports/', ReportListCreate.as_view(), name='slr10-reports'),
    path('reports/<uuid:pk>/', ReportDetail.as_view(), name='slr10-report-detail'),
    path('reports/<uuid:pk>/evidence/', EvidenceListUpload.as_view(), name='slr10-evidence'),
    path('reports/<uuid:pk>/bundles/', BundleCreateView.as_view(), name='slr10-bundle'),
    path('evidence/<uuid:pk>/media/', EvidenceMedia.as_view(), name='slr10-media'),
]
