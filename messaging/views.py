from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models import Count
from accounts.models import User
from jobs.models import Application
from .models import Message, Notification, Conversation

@login_required
def inbox(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    
    # Enrich conversations with other user and last message
    for convo in conversations:
        convo.other_user = convo.participants.exclude(id=request.user.id).first()
        last_msg = convo.messages.order_by('-timestamp').first()
        convo.last_message = last_msg.content if last_msg else "No messages yet"

    return render(request, 'messaging/inbox.html', {'conversations': conversations})

@login_required
def chat_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Access check
    if request.user not in conversation.participants.all():
         return redirect('inbox')

    # Handle POST (New Message)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            # conversation.updated_at is auto-updated due to auto_now=True
            conversation.save() 
            return redirect('chat_view', conversation_id=conversation.id)

    messages_qs = conversation.messages.order_by('timestamp')
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    # Check if current user has ever sent a message in this conversation
    has_user_sent = messages_qs.filter(sender=request.user).exists()

    return render(request, 'messaging/chat.html', {
        'messages': messages_qs,
        'other_user': other_user,
        'conversation': conversation,
        'has_user_sent': has_user_sent
    })

@login_required
def start_chat(request, user_id):
    # Helper to find/create conversation 
    other_user = get_object_or_404(User, id=user_id)
    
    # Find existing conversation
    # Filter for conversations where both users are participants
    # This logic ensures we find a conversation that has exactly these two participants?
    # Simple approach: find user's conversations, then filter for other_user
    my_convos = Conversation.objects.filter(participants=request.user)
    start_convo = my_convos.filter(participants=other_user).first()
    
    if not start_convo:
        start_convo = Conversation.objects.create()
        start_convo.participants.add(request.user, other_user)
    
    return redirect('chat_view', conversation_id=start_convo.id)

@login_required
def notifications_view(request):
    # Allow all users to see notifications
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Mark all as read
    for note in notes.filter(is_read=False):
        note.is_read = True
        note.save()

    return render(request, 'messaging/notifications.html', {'notifications': notes})



@login_required
def generate_reply(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    user_type = request.user.user_type
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    # Get last message from OTHER user to provide context
    last_message = conversation.messages.exclude(sender=request.user).order_by('-timestamp').first()
    last_content = last_message.content.lower() if last_message else ""

    if user_type == 'recruiter':
        # ... (Recruiter logic remains similar or can be enhanced later) ...
        reply_text = (
            f"Hello {other_user.username},\n\n"
            "Thank you for your application and interest in our company. "
            "I have reviewed your profile and was impressed by your experience.\n\n"
            "We would like to move forward with the next steps. Please let me know your availability for a brief discussion this week regarding the role.\n\n"
            "Looking forward to hearing from you."
        )
    else: # JOB SEEKER LOGIC (Enhanced)
        
        # 1. Check for Availability Request
        if any(w in last_content for w in ['available', 'time', 'when', 'schedule']):
            reply_text = (
                f"Hi {other_user.username},\n\n"
                "Thank you for following up. I am definitely interested in discussing this further.\n\n"
                "I am available this Tuesday or Thursday afternoon (after 2 PM). Please let me know if either of those works for you, or feel free to suggest another time.\n\n"
                "Best regards,"
            )
        
        # 2. Check for Interview/Call Request
        elif any(w in last_content for w in ['interview', 'call', 'chat', 'meet']):
            reply_text = (
                f"Hi {other_user.username},\n\n"
                "Thank you for reaching out. I would be happy to discuss the role and my experience in more detail.\n\n"
                "Please let me know how you would like to proceed with the scheduling.\n\n"
                "Best regards,"
            )
            
        # 3. Default / Informational Acknowledgment
        else:
            # Fallback to the original "Interest" template if no specific context
            latest_app = Application.objects.filter(applicant=request.user, job__recruiter=other_user).order_by('-applied_on').first()
            job_title = latest_app.job.title if latest_app else "the position"

            reply_text = (
                f"Dear {other_user.username},\n\n"
                f"Thank you for connecting. I am very interested in the {job_title} role at your company.\n\n"
                "My background aligns well with the requirements, and I would appreciate the opportunity to discuss how I can contribute to your team.\n\n"
                "Best regards,"
            )

    return JsonResponse({'reply': reply_text})
