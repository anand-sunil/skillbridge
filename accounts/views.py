from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import HttpResponse


from .forms import JobSeekerSignUpForm, RecruiterSignUpForm, LoginForm

# ✅ IMPORT MODELS (THIS WAS MISSING)
from jobs.models import Job, Application, SavedJob
from .models import User


from django.utils import timezone
from courses.models import Course

# ------------------ HOME ------------------
def home(request):
    # Featured Jobs (Latest 3)
    featured_jobs = Job.objects.order_by('-posted_on')[:6]

    # Featured Courses (Active & Not Expired, Latest 6)
    # Note: Complex verified featured logic can be added here. 
    # For now, simplest robust query:
    featured_courses = Course.objects.filter(
        is_active=True, 
        expires_on__gte=timezone.now().date()
    ).order_by('-created_at')[:6]



    # Dynamic Data for Hero/Stats
    latest_job = Job.objects.order_by('-posted_on').first()
    latest_course = Course.objects.filter(is_active=True).order_by('-created_at').first()
    
    context = {
        'featured_jobs': featured_jobs,
        'featured_courses': featured_courses,
        'latest_job': latest_job,
        'latest_course': latest_course,
        'stats': {
            'jobs_count': Job.objects.count(),
            'courses_count': Course.objects.filter(is_active=True).count(),
            'recruiters_count': User.objects.filter(user_type='recruiter').count(),
            'seekers_count': User.objects.filter(user_type='job_seeker').count(),
        }
    }

    return render(request, 'accounts/home.html', context)


# ------------------ UNIVERSAL SIGNUP PAGE ------------------
def register_view(request):
    """
    This supports your register.html which expects:
    - username
    - email
    - password1
    - password2
    - user_type (job_seeker / recruiter)
    """

    if request.method == 'POST':
        user_type = request.POST.get("user_type")

        # Choose correct form based on role
        if user_type == "job_seeker":
            form = JobSeekerSignUpForm(request.POST)
        elif user_type == "recruiter":
            form = RecruiterSignUpForm(request.POST)
        else:
            messages.error(request, "Please select a valid user type.")
            return redirect('signup')

        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Account created successfully!")
            return redirect('home')

    else:
        form = JobSeekerSignUpForm()  # default empty form

    return render(request, 'accounts/register.html', {'form': form})


# ------------------ SPECIFIC REGISTER PAGES ------------------
def register_jobseeker(request):
    if request.method == 'POST':
        form = JobSeekerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Account created successfully as Job Seeker!")
            return redirect('home')
    else:
        form = JobSeekerSignUpForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'role': 'jobseeker'
    })


def register_recruiter(request):
    if request.method == 'POST':
        form = RecruiterSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Account created successfully as Recruiter!")
            return redirect('home')
    else:
        form = RecruiterSignUpForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'role': 'recruiter'
    })


# ------------------ LOGIN ------------------
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")

            return redirect('home')  # ✅ ALWAYS HOME

    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


# ------------------ LOGOUT ------------------
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You’ve been logged out.")
    return redirect('home')


# ------------------ JOB SEEKER DASHBOARD ------------------
@login_required
def jobseeker_dashboard(request):
    if request.user.user_type != 'job_seeker':
        return HttpResponseForbidden("Access denied: Only Job Seekers can view this page.")

    # All applications by this user
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_on')

    # Saved jobs
    saved_jobs = SavedJob.objects.filter(user=request.user)

    # Counts
    applied_jobs_count = applications.count()
    saved_jobs_count = saved_jobs.count()
    notifications_count = 0  # Add notifications system later

    # Recent applications (latest 5)
    recent_applications = applications[:5]

    # Recommended jobs (simple logic: show jobs not applied to)
    recommended_jobs = Job.objects.exclude(applications__applicant=request.user).order_by('-posted_on')[:4]

    context = {
        "applied_jobs_count": applied_jobs_count,
        "saved_jobs_count": saved_jobs_count,
        "notifications_count": notifications_count,
        "recent_applications": recent_applications,
        "recommended_jobs": recommended_jobs,
    }

    return render(request, "accounts/jobseeker_dashboard.html", context)


# ------------------ RECRUITER DASHBOARD ------------------
@login_required
def recruiter_dashboard(request):
    if request.user.user_type != 'recruiter':
        return HttpResponseForbidden("Access denied: Only Recruiters can view this page.")

    # Core Stats
    posted_jobs = Job.objects.filter(recruiter=request.user)
    job_count = posted_jobs.count()

    # All applications for jobs posted by this recruiter
    # We can query Application directly by filtering on job__recruiter
    recruiter_apps = Application.objects.filter(job__recruiter=request.user)
    total_applications = recruiter_apps.count()

    # New applications today
    from django.utils import timezone
    today = timezone.now().date()
    # Filter by applied_on__date since applied_on is DateTimeField
    new_today = recruiter_apps.filter(applied_on__date=today).count()

    # Recent applications (latest 5)
    recent_apps = recruiter_apps.order_by('-applied_on')[:5]

    try:
        from messaging.models import Notification
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    except ImportError:
        unread_count = 0

    context = {
        "job_count": job_count,
        "total_applications": total_applications,
        "new_today": new_today,
        "recent_apps": recent_apps,
        "unread_count": unread_count,
    }

    return render(request, 'accounts/recruiter_dashboard.html', context)

@login_required
def saved_jobs_view(request):
    if request.user.user_type != 'job_seeker':
        return HttpResponseForbidden("Access denied: Only Job Seekers can view this page.")

    saved = SavedJob.objects.filter(user=request.user).select_related("job")

    return render(request, "accounts/saved_jobs.html", {
        "saved_jobs": saved
    })

@login_required
def recruiter_applications(request):
    if request.user.user_type != 'recruiter':
        return HttpResponseForbidden("Access denied. Recruiters only.")
    
    # Fetch all applications for jobs posted by this recruiter
    applications = Application.objects.filter(job__recruiter=request.user).select_related('job', 'applicant').order_by('-applied_on')
    
    return render(request, "accounts/recruiter_applications.html", {
        "applications": applications
    })

def messages_placeholder(request):
    return redirect('inbox')

@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")

@login_required
def profile_edit(request):
    if request.method == "POST":
        request.user.username = request.POST.get("username")
        request.user.email = request.POST.get("email")
        
        if "avatar" in request.FILES:
            request.user.avatar = request.FILES["avatar"]
            
        request.user.save()
        
        # Update extra profile fields
        if request.user.user_type == 'job_seeker':
            profile = request.user.jobseekerprofile
            profile.bio = request.POST.get("bio", "")
            profile.skills = request.POST.get("skills", "")
            if "resume" in request.FILES:
                profile.resume = request.FILES["resume"]
            profile.save()
            
        elif request.user.user_type == 'recruiter':
            profile = request.user.recruiterprofile
            profile.company_name = request.POST.get("company_name", "")
            profile.company_website = request.POST.get("company_website", "")
            profile.company_description = request.POST.get("company_description", "")
            profile.save()

        messages.success(request, "Profile updated successfully")
        return redirect("profile")

    return render(request, "accounts/profile_edit.html")

@login_required
def application_detail(request, application_id):
    application = get_object_or_404(
        Application,
        id=application_id,
        applicant=request.user
    )

    return render(
        request,
        "accounts/application_detail.html",
        {"application": application}
    )

@login_required
def my_applications(request):
    if request.user.user_type != 'job_seeker':
        return HttpResponseForbidden("Access denied. Job Seekers only.")

    applications = Application.objects.filter(applicant=request.user).select_related('job', 'job__recruiter').order_by('-applied_on')

    return render(request, "accounts/my_applications.html", {
        "applications": applications
    })

@login_required
def seeker_profile(request, user_id):
    # Only recruiters can view job seeker profiles
    if request.user.user_type != 'recruiter':
        messages.error(request, "Access denied. Recruiters only.")
        return redirect('home')

    seeker = get_object_or_404(User, id=user_id)
    
    # Optional: Check if this seeker has applied to any of the recruiter's jobs?
    # For now, open access for recruiters is fine as per requirements.

    return render(request, "accounts/seeker_profile.html", {"seeker": seeker})