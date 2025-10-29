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
    path('daily/<int:year>/<int:month>/<int:day>/pdf/', views.daily_schedule_pdf_view, name='daily_detail_pdf'),
    path('staff/<int:pk>/analytics/<int:year>/<int:month>/', views.StaffAnalyticsView.as_view(), name='staff_analytics'),
    path('monthly-assignments/', views.MonthlyAssignmentListView.as_view(), name='monthly_assignment_list'),
    path('monthly-assignments/new/', views.MonthlyAssignmentCreateView.as_view(), name='monthly_assignment_create'),
    path('monthly-assignments/<int:pk>/edit/', views.MonthlyAssignmentUpdateView.as_view(), name='monthly_assignment_edit'),
    path('monthly-assignments/<int:pk>/delete/', views.MonthlyAssignmentDeleteView.as_view(), name='monthly_assignment_delete'),
    path('checklist/', views.ChecklistView.as_view(), name='checklist'),
    path('manager-review/', views.ManagerReviewView.as_view(), name='manager_review'),
    path('appraisal/', views.AppraisalAnalyticsView.as_view(), name='appraisal_analytics'),
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_edit'),
    path('monthly-assignments/<int:year>/<int:month>/', views.MonthlyAssignmentDisplayView.as_view(), name='monthly_assignment_display'),
    path('monthly-assignments/bulk-assign/<int:year>/<int:month>/', views.MonthlyAssignmentBulkAssignView.as_view(), name='monthly_assignment_bulk_assign'),
    path('monthly-assignments/today/', views.MonthlyAssignmentTodayRedirectView.as_view(), name='monthly_assignment_today'),
]