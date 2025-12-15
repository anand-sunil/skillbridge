from django.contrib import admin
from django.urls import path, include
from accounts import views as acc_views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('', acc_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('messages/', include('messaging.urls')),
    path('courses/', include('courses.urls')),
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name="accounts/password_reset_form.html"
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name="accounts/password_reset_done.html"
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name="accounts/password_reset_confirm.html"
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name="accounts/password_reset_complete.html"
         ),
         name='password_reset_complete'),

    path("jobs/", include("jobs.urls")),

]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

