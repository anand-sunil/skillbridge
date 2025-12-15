from django.contrib import admin
from .models import User, JobSeekerProfile, RecruiterProfile

admin.site.register(User)
admin.site.register(JobSeekerProfile)
admin.site.register(RecruiterProfile)
