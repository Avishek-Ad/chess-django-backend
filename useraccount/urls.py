from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserCreateView.as_view(), name='user-register'),
    path('dashboard/stats/', views.UserDashboardStatsView.as_view(), name="user-dashboard-stats")
]
