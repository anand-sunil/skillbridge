from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import Course, CoursePayment, CourseListingPlan

@login_required # Optional, depending on if public can see courses
def course_list(request):
    """
    Public View: Show only active courses that haven't expired.
    """
    today = timezone.now().date()
    courses = Course.objects.filter(
        is_active=True,
        expires_on__gte=today
    ).order_by('-created_at')
    
    return render(request, "courses/course_list.html", {"courses": courses})

@login_required
def add_course(request):
    """
    Provider View: Add details -> Redirect to Payment
    """
    # Simple check if user is allowed to be a provider (e.g. Recruiter)
    # The requirement says "Course Provider (any authenticated user for now)"
    # but let's keep it safe or open as requested. User said "any authenticated user for now"
    # but in previous steps we restricted to 'recruiter'. 
    # The prompt says "Course Provider (any authenticated user for now)".
    # I will stick to the user's explicit prompt requirement "any authenticated user".
    
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        instructor = request.POST.get("instructor")
        duration = request.POST.get("duration") # Matches form name='duration'
        external_link = request.POST.get("external_link")

        # Create inactive course
        course = Course.objects.create(
            provider=request.user,
            title=title,
            description=description,
            instructor=instructor,
            # Note: Model has duration_text & duration_days. 
            # We map form 'duration' to duration_text for display.
            # duration_days is mandatory in model but form might be text. 
            # I'll set default 0 or try to parse. 
            # The prompt Add Course Requirements: "enter title... duration"
            # Model has duration_days (int) AND duration_text (char).
            # I will fill duration_text with the input and default days to 0 until payment plan sets it? 
            # OR the model in the prompt showed `duration_days` as a field. 
            # I will set `duration_text` from input and `duration_days` to 0 (to be set by plan).
            
            duration_text=str(duration),
            duration_days=0, 
            
            external_link=external_link,
            is_active=False
        )
        
        return redirect("course_payment", course_id=course.id)

    return render(request, "courses/add_course.html")

@login_required
def course_payment(request, course_id):
    """
    Step 1: Select Plan
    """
    course = get_object_or_404(Course, id=course_id)
    
    if course.provider != request.user:
        messages.error(request, "You cannot pay for a course you do not own.")
        return redirect("course_list")

    return render(request, "courses/course_payment.html", {"course": course})


@login_required
def payment_checkout(request, course_id):
    """
    Step 2: Mock Payment Gateway & Activation
    """
    course = get_object_or_404(Course, id=course_id)
    
    if course.provider != request.user:
        return redirect("home")

    if request.method == "POST":
        # Check if coming from Plan Selection (has 'plan' but not 'pay') OR logic to distinguish
        # We can detect if it's the final pay submit.
        # But wait, the plan says: POST from Plan Selection -> Render Checkout. POST from Checkout -> Activate.
        
        plan_days = request.POST.get("plan")
        if not plan_days:
            messages.error(request, "Please select a plan.")
            return redirect("course_payment", course_id=course.id)
            
        plan_days = int(plan_days)
        price_map = {7: 499, 15: 899, 30: 1499}
        amount = price_map.get(plan_days, 499)

        # A simple way to distinguish steps: The Checkout Page Form will NOT set a specific flag?
        # Actually it does: standard POST.
        # But the Plan Page also POSTs to this view.
        # We can distinguish by "is_final_payment" hidden field OR just verify if we are rendering or processing.
        # Plan Page sends `plan`. Checkout Page sends `plan` AND `card_number` (or just assume validation).
        # Let's check for a field unique to the payment form? e.g. "Card Number" dummy check?
        # OR better: The Plan Page POSTs to THIS view to RENDER the checkout.
        # The Checkout Page POSTs to THIS view to PROCESS.
        # How to distinguish?
        # WE CAN'T easily unless we check for card data.
        
        # Let's assume if 'confirm_pay' is present (button name) or similar?
        # Or just check request.path? No.
        # Let's use a query param or hidden field in the checkout form. 
        # I'll add a hidden input "action=pay" to the checkout form template I created? 
        # Wait, I didn't add that in the template. 
        # I'll check for 'card_number' presence (mock check) since I know I put it in the HTML but gave it no name? 
        # Looking at my template: <input type="text" placeholder="John Doe" ...> NO NAME ATTRIBUTES on the payment fields!
        # Ah, mock payment.
        # The form on `payment_checkout.html` has: <input type="hidden" name="plan" value="{{ plan }}">
        # And the button is just submit.
        # The inputs have NO name attributes (except plan). So they won't even be in POST data!
        # Good, that keeps secrets out of server logs.
        # But then how do I know it's the final step?
        # The Plan Selection page sends `plan`.
        # The Checkout Page sends `plan`.
        # They look IDENTICAL to the server.
        # FIX: I need to add a hidden field `step='process'` to the checkout template form.
        # OR: I can check the referer? No, unreliable.
        # OR: I can assume if I'm receiving a POST, I should RENDER checkout?
        # But the checkout form ALSO POSTS!
        
        # Update plan:
        # I will update the `payment_checkout.html` to include details like `name="process_payment"` on the button.
        # Then I can check `if 'process_payment' in request.POST`.
        
        if 'process_payment' in request.POST:
            # ACTIVATE
            plan_name_map = {7: "Basic", 15: "Standard", 30: "Premium"}
            plan_obj, _ = CourseListingPlan.objects.get_or_create(
                duration_days=plan_days,
                defaults={
                    'name': plan_name_map.get(plan_days, "Custom"),
                    'price': amount,
                    'is_featured': (plan_days > 7)
                }
            )
            
            CoursePayment.objects.create(
                course=course,
                provider=request.user,
                plan=plan_obj,
                paid_amount=amount,
                is_active=True,
                end_date=timezone.now() + timedelta(days=plan_days) 
            )

            course.is_active = True
            course.expires_on = (timezone.now() + timedelta(days=plan_days)).date()
            course.plan_days = plan_days
            course.amount_paid = amount
            course.save()
            
            return render(request, "courses/payment_success.html", {"course": course})

        else:
            # DISPLAY CHECKOUT
            return render(request, "courses/payment_checkout.html", {
                "course": course,
                "plan": plan_days,
                "price": amount
            })

    # If GET, redirect back to plan selection
    return redirect("course_payment", course_id=course.id)

@login_required
def provider_dashboard(request):
    """
    Provider Stats & Management
    """
    courses = Course.objects.filter(provider=request.user).order_by('-created_at')
    today = timezone.now().date()
    
    # Simple Auto-Expiry Check on Load
    # (Ideally done via cron, but View-based is fine for MVP)
    for c in courses:
        if c.is_active and c.expires_on and c.expires_on < today:
            c.is_active = False
            c.save()

    total_courses = courses.count()
    active_courses = courses.filter(is_active=True).count()
    expired_courses = courses.filter(is_active=False).count()
    
    # Calculate days left for active courses
    # We can pass this as a proeprty or annotate
    # For simplicity in template: use {{ course.expires_on|timeuntil }} or calculate here
    
    return render(request, "courses/provider_dashboard.html", {
        "courses": courses,
        "total_courses": total_courses,
        "active_courses": active_courses,
        "expired_courses": expired_courses
    })