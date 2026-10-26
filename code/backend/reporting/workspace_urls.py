from django.urls import path
from . import workspace_views as views

urlpatterns = [
    path('dashboard/', views.Dashboard.as_view()),
    path('reports/', views.ReportList.as_view()),
    path('reports/<uuid:pk>/', views.ReportDetail.as_view()),
    path('reports/<uuid:pk>/claim/', views.ClaimView.as_view()),
    path('reports/<uuid:pk>/assignment/', views.AssignmentView.as_view()),
    path('reports/<uuid:pk>/reviews/', views.ReviewView.as_view()),
    path('reports/<uuid:pk>/followups/', views.FollowupView.as_view()),
    path('reports/<uuid:pk>/followups/<uuid:followup_id>/', views.FinishFollowupView.as_view()),
    path('reports/<uuid:pk>/decision/', views.DecisionView.as_view()),
    path('reports/<uuid:pk>/close/', views.CloseView.as_view()),
    path('assignment-targets/', views.Targets.as_view()),
    path('audit/', views.Audit.as_view()),
    path('services/', views.Monitoring.as_view()),
]
