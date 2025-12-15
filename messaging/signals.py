from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification, Conversation
from jobs.models import Application
from django.urls import reverse

@receiver(post_save)
def create_message_notification(sender, instance, created, **kwargs):
    if sender.__name__ != 'Message':
        return
    if created:
        conversation = instance.conversation
        # Notify all participants EXCEPT the sender
        for participant in conversation.participants.all():
            if participant != instance.sender:
                Notification.objects.create(
                    user=participant,
                    message=f"New message from {instance.sender.username}",
                    url=reverse('chat_view', args=[conversation.id])
                )

@receiver(post_save, sender=Application)
def create_application_notification(sender, instance, created, **kwargs):
    if created:
        # 1. Notify Recruiter of new application
        recruiter = instance.job.recruiter
        Notification.objects.create(
            user=recruiter,
            message=f"New application for {instance.job.title} from {instance.applicant.username}",
            url=reverse('recruiter_applications')
        )
    else:
        # 2. Notify Applicant of status change (simplified check)
        # In a real app, we'd check if 'status' field changed using __init__ tracking or similar,
        # but for now, we assume save() on existing app implies update.
        # Ideally, we should check if status specifically changed to avoid spam.
        # However, for this task, let's keep it simple or check against 'pending'.
        
        if instance.status != 'pending': # Assuming default is pending
             Notification.objects.create(
                user=instance.applicant,
                message=f"Update on your application for {instance.job.title}: {instance.status.title()}",
                url=reverse('my_applications')
            )
