from django.urls import path
from . import views

urlpatterns = [
    # Job listings page (main page)
    path("", views.job_list, name="job_list"),

    # Post job (recruiters only)
    path("post/", views.post_job, name="post_job"),

    # Apply for a job
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),

    # Save / Unsave job
    path("save/<int:job_id>/", views.save_job, name="save_job"),

    path("<int:job_id>/", views.job_detail, name="job_detail"),

    path("saved/", views.saved_jobs, name="saved_jobs"),


    # Recruiter actions
    path("post/", views.post_job, name="post_job"),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("job/<int:job_id>/applicants/", views.view_applicants, name="view_applicants"),
    
    # Recruiter Applicant Management (New)
    path("recruiter/jobs/", views.recruiter_jobs, name="recruiter_jobs"),
    path("job/<int:job_id>/applications/", views.job_applicants, name="job_applicants"),

    path("application/<int:application_id>/", views.applicant_detail, name="applicant_detail"),
    path("applications/accept/<int:application_id>/", views.accept_application, name="accept_application"),
    path("applications/reject/<int:application_id>/", views.reject_application, name="reject_application"),

    path("delete/<int:job_id>/", views.delete_job, name="delete_job"),
    path("edit/<int:job_id>/", views.edit_job, name="edit_job"),

]
