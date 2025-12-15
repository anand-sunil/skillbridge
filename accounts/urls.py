from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # REGISTER (Main signup page)
    path('register/', views.register_view, name='signup'),

    # Separate signup pages (optional)
    path('register/jobseeker/', views.register_jobseeker, name='register_jobseeker'),
    path('register/recruiter/', views.register_recruiter, name='register_recruiter'),

    # Login / Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/jobseeker/', views.jobseeker_dashboard, name='jobseeker_dashboard'),
    path('dashboard/recruiter/', views.recruiter_dashboard, name='recruiter_dashboard'),

    path('saved-jobs/', views.saved_jobs_view, name='saved_jobs'),
    path('recruiter/applications/', views.recruiter_applications, name='recruiter_applications'),
    path("messages/", views.messages_placeholder, name="messages_redirect"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path(
    "applications/<int:application_id>/",
    views.application_detail,
    name="application_detail"),
    path("applications/", views.my_applications, name="my_applications"),
    path("seeker-profile/<int:user_id>/", views.seeker_profile, name="seeker_profile"),



]
