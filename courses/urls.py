from django.urls import path
from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("add/", views.add_course, name="add_course"),
    path("payment/<int:course_id>/", views.course_payment, name="course_payment"),
    path("payment/checkout/<int:course_id>/", views.payment_checkout, name="payment_checkout"),
    path("provider/dashboard/", views.provider_dashboard, name="provider_dashboard"),
]
