# In main_app/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordChangeView
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', views.IndexRedirectView.as_view(), name='index'),
    path('roster/<int:year>/<int:month>/', views.MonthlyRosterView.as_view(), name='monthly_roster'),
    path('shift/new/', views.ShiftCreateView.as_view(), name='create_shift'),
    path('shift/new/<int:staff_id>/', views.ShiftCreateView.as_view(), name='create_shift_for_staff'),
    path('shift/<int:pk>/edit/', views.ShiftUpdateView.as_view(), name='edit_shift'),
    path('shift/<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='delete_shift'),
    path('staff/new/', views.UserCreateView.as_view(), name='create_user'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('daily/<int:year>/<int:month>/<int:day>/', views.DailyDetailView.as_view(), name='daily_detail'),
    path('my-schedule/', views.MyScheduleView.as_view(), name='my_schedule'),
    path('daily-assign/', views.DailyAssignRedirectView.as_view(), name='daily_assign_redirect'),
    path('daily-assign/<int:year>/<int:month>/<int:day>/', views.DailyAssignView.as_view(), name='daily_assign'),
    path('bulk-assign/', views.BulkAssignView.as_view(), name='bulk_assign'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('password-change/',PasswordChangeView.as_view(template_name='password_change_form.html',success_url='/password-change/done/'),name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),name='password_change_done'),
]