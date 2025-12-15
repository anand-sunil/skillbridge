from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Job, Application, SavedJob
from accounts.models import User


# ----------------------------------------------------
# POST JOB - Recruiters only
# ----------------------------------------------------
@login_required
def post_job(request):
    if request.user.user_type != 'recruiter':
        messages.error(request, "Only recruiters can post jobs.")
        return redirect('home')

    if request.method == 'POST':

        title = request.POST["title"].strip()
        description = request.POST["description"].strip()
        location = request.POST["location"].strip()
        salary_raw = request.POST.get("salary", "").strip()
        deadline = request.POST.get("deadline", None)

        # Required checks
        if not title or not description or not location:
            messages.error(request, "Please fill all required fields.")
            return redirect("post_job")

        # Convert salary properly
        salary = salary_raw if salary_raw else None

        Job.objects.create(
            recruiter=request.user,
            title=title,
            description=description,
            location=location,
            salary=salary,
            deadline=deadline
        )

        messages.success(request, "Job posted successfully!")
        return redirect("job_list")

    return render(request, "jobs/post_job.html")


# ----------------------------------------------------
# JOB LIST + FILTERS
# ----------------------------------------------------
@login_required
def job_list(request):
    search = request.GET.get("search", "")
    location = request.GET.get("location", "")
    salary = request.GET.get("salary", "")
    job_type = request.GET.get("job_type", "")

    jobs = Job.objects.all().order_by("-posted_on")

    # ---------------- SEARCH ----------------
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    # ---------------- LOCATION FILTER ----------------
    if location and location != "all":
        jobs = jobs.filter(location__icontains=location)

    # ---------------- SALARY FILTER ----------------
    if salary == "10-20":
        jobs = jobs.filter(salary__gte=10000, salary__lte=20000)

    elif salary == "20-40":
        jobs = jobs.filter(salary__gte=20000, salary__lte=40000)

    elif salary == "40+":
        jobs = jobs.filter(salary__gte=40000)

    # ---------------- JOB TYPE FILTER ----------------
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    # ---------------- SAVED JOBS (for UI heart icon) ----------------
    saved_job_ids = []
    if request.user.is_authenticated and request.user.user_type == "job_seeker":
        saved_job_ids = list(
            SavedJob.objects.filter(user=request.user).values_list("job_id", flat=True)
        )

    return render(request, "jobs/job_list.html", {
        "jobs": jobs,
        "saved_job_ids": saved_job_ids
    })


# ----------------------------------------------------
# APPLY JOB - Job Seekers only
# ----------------------------------------------------
@login_required
def apply_job(request, job_id):
    if request.user.user_type != 'job_seeker':
        messages.error(request, "Only job seekers can apply for jobs.")
        return redirect('home')

    job = get_object_or_404(Job, id=job_id)

    # Check duplicate application
    existing = Application.objects.filter(job=job, applicant=request.user).first()
    if existing:
        messages.warning(request, "You have already applied for this job.")
        return redirect('job_list')

    if request.method == "POST":
        # Create new application
        resume_file = None
        
        # 1. Try uploaded file
        if "resume" in request.FILES:
            resume_file = request.FILES["resume"]
        
        # 2. Fallback to profile resume
        elif hasattr(request.user, 'jobseekerprofile') and request.user.jobseekerprofile.resume:
            resume_file = request.user.jobseekerprofile.resume
            
        Application.objects.create(
            job=job,
            applicant=request.user,
            resume=resume_file
        )

        # Optional - Recruiter notification
        try:
            from messaging.models import Notification
            Notification.objects.create(
                user=job.recruiter,
                message=f"{request.user.username} applied for your job: {job.title}",
                url=f"/jobs/job/{job.id}/applicants/"
            )
        except:
            pass  # ignore if messaging app not added yet

        messages.success(request, f"You’ve successfully applied for {job.title}!")
        return redirect('job_list')

    return render(request, "jobs/apply_job.html", {"job": job})


# ----------------------------------------------------
# SAVE JOB / UNSAVE JOB (Toggle)
# ----------------------------------------------------
@login_required
def save_job(request, job_id):
    if request.user.user_type != "job_seeker":
        messages.error(request, "Only job seekers can save jobs.")
        return redirect("job_list")

    job = get_object_or_404(Job, id=job_id)

    saved = SavedJob.objects.filter(user=request.user, job=job).first()

    if saved:
        saved.delete()
        messages.info(request, f"Removed from saved jobs: {job.title}")
    else:
        SavedJob.objects.create(user=request.user, job=job)
        messages.success(request, f"Saved job: {job.title}")

    return redirect("job_list")

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    is_saved = False
    if request.user.user_type == "job_seeker":
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "is_saved": is_saved
    })

@login_required
def saved_jobs(request):
    if request.user.user_type != "job_seeker":
        messages.error(request, "Only job seekers can view saved jobs.")
        return redirect("home")

    saved = SavedJob.objects.filter(user=request.user).select_related("job")

    return render(request, "jobs/saved_jobs.html", {
        "saved_jobs": saved
    })

# ----------------------------------------------------
# RECRUITER MANAGE JOBS
# ----------------------------------------------------
@login_required
def my_jobs(request):
    if request.user.user_type != 'recruiter':
        messages.error(request, "Access denied. Recruiters only.")
        return redirect('home')

    jobs = Job.objects.filter(recruiter=request.user).order_by('-posted_on')
    return render(request, "jobs/recruiter_jobs.html", {
        "jobs": jobs
    })


@login_required
def view_applicants(request, job_id):
    # 1. Fetch job and ensure ownership
    job = get_object_or_404(Job, id=job_id)

    if request.user.user_type != 'recruiter':
        messages.error(request, "Access denied. Recruiters only.")
        return redirect('home')

    if job.recruiter != request.user:
        messages.error(request, "Access denied. You do not own this job.")
        return redirect('my_jobs')

    # 2. Fetch applications
    applications = Application.objects.filter(job=job).select_related('applicant').order_by('-applied_on')

    # 3. Render template with context
    return render(request, "jobs/view_applicants.html", {
        "job": job,
        "applications": applications
    })





@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if job.recruiter != request.user:
        messages.error(request, "You are not authorized to delete this job.")
        return redirect('my_jobs')

    job.delete()
    messages.success(request, "Job deleted successfully.")
    return redirect('my_jobs')


@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, recruiter=request.user)

    if request.method == "POST":
        job.title = request.POST["title"]
        job.description = request.POST["description"]
        job.location = request.POST["location"]

        salary_raw = request.POST.get("salary", "").strip()
        job.salary = salary_raw if salary_raw else None

        job.deadline = request.POST.get("deadline") or None
        job.save()

        messages.success(request, "Job updated successfully!")
        return redirect("my_jobs")

    return render(request, "jobs/edit_job.html", {"job": job})

@login_required
def recruiter_jobs(request):
    if request.user.user_type != 'recruiter':
        messages.error(request, "Access denied. Recruiters only.")
        return redirect('home')

    jobs = Job.objects.filter(recruiter=request.user).order_by('-posted_on')
    return render(request, "jobs/recruiter_jobs.html", {
        "jobs": jobs
    })


@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.user.user_type != 'recruiter':
        return HttpResponseForbidden("Access denied. Recruiters only.")

    if job.recruiter != request.user:
        return HttpResponseForbidden("Access denied. You do not own this job.")

    applications = Application.objects.filter(job=job).select_related('applicant').order_by('-applied_on')

    return render(request, "jobs/job_applicants.html", {
        "job": job,
        "applications": applications
    })


@login_required
def applicant_detail(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    if request.user.user_type != 'recruiter' or application.job.recruiter != request.user:
        return HttpResponseForbidden("Access denied. You do not own this application.")

    return render(request, "jobs/applicant_detail.html", {
        "application": application
    })


@login_required
def accept_application(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    if request.user.user_type != 'recruiter' or application.job.recruiter != request.user:
        return HttpResponseForbidden("Access denied. You do not own this application.")

    if application.status in ['accepted', 'rejected']:
        messages.warning(request, "This application has already been processed.")
        return redirect('job_applicants', job_id=application.job.id)

    application.status = 'accepted'
    application.save()
    
    messages.success(request, f"Application for {application.applicant.username} accepted.")
    return redirect('job_applicants', job_id=application.job.id)


@login_required
def reject_application(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    if request.user.user_type != 'recruiter' or application.job.recruiter != request.user:
        return HttpResponseForbidden("Access denied. You do not own this application.")

    if application.status in ['accepted', 'rejected']:
        messages.warning(request, "This application has already been processed.")
        return redirect('job_applicants', job_id=application.job.id)

    application.status = 'rejected'
    application.save()
    
    messages.warning(request, f"Application for {application.applicant.username} rejected.")
    return redirect('job_applicants', job_id=application.job.id)
