# courses/admin.py
from django.contrib import admin
from .models import Course, CourseListingPlan, CoursePayment

admin.site.register(Course)
admin.site.register(CourseListingPlan)
admin.site.register(CoursePayment)
