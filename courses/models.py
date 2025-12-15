from django.db import models
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class Course(models.Model):
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="courses"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.CharField(max_length=150)

    duration_text = models.CharField(max_length=100, default="Unknown")
    duration_days = models.PositiveIntegerField(default=0)

    external_link = models.URLField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    expires_on = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_status(self):
        active_payment = self.coursepayment_set.filter(
            is_active=True,
            end_date__gte=now()
        ).first()

        if active_payment:
            self.is_active = True
            self.expires_on = active_payment.end_date.date()
        else:
            self.is_active = False

        self.save(update_fields=["is_active", "expires_on"])

    def __str__(self):
        return self.title


class CourseListingPlan(models.Model):
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class CoursePayment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    provider = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(CourseListingPlan, on_delete=models.CASCADE)

    paid_amount = models.DecimalField(max_digits=8, decimal_places=2)

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = now() + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
        self.course.update_status()

    def __str__(self):
        return f"{self.course.title} ({self.plan.name})"
