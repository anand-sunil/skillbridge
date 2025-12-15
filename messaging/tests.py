from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class MessagingTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.client = Client()

    def test_start_chat_creates_conversation(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(f'/messages/start/{self.user2.id}/')
        
        # Should redirect to chat view
        self.assertEqual(response.status_code, 302)
        
        # Check conversation created
        convo = Conversation.objects.filter(participants=self.user1).filter(participants=self.user2).first()
        self.assertIsNotNone(convo)
        self.assertEqual(convo.participants.count(), 2)
        
        # Verify redirect url
        expected_url = f'/messages/chat/{convo.id}/'
        self.assertRedirects(response, expected_url)

    def test_start_chat_reuses_conversation(self):
        # Create initial conversation
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        
        self.client.login(username='user1', password='password123')
        response = self.client.get(f'/messages/start/{self.user2.id}/')
        
        # Should redirect to SAME conversation
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertRedirects(response, f'/messages/chat/{convo.id}/')

    def test_send_message(self):
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        
        self.client.login(username='user1', password='password123')
        response = self.client.post(f'/messages/chat/{convo.id}/', {'content': 'Hello World'})
        
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.content, 'Hello World')
        self.assertEqual(msg.sender, self.user1)
        self.assertEqual(msg.conversation, convo)

    def test_inbox_view(self):
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=convo, sender=self.user2, content="Hi there")
        
        self.client.login(username='user1', password='password123')
        response = self.client.get('/messages/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hi there")
        self.assertContains(response, "user2")

    def test_generate_reply(self):
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        
        self.client.login(username='user1', password='password123')
        # user1 is jobseeker/default? We didn't set profile in test setup but logic relies on request.user.user_type
        # Accounts model sets default 'job_seeker'.
        response = self.client.get(f'/messages/generate-reply/{convo.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('reply', response.json())
        self.assertIn('Dear Hiring Manager', response.json()['reply'])

    def test_generate_reply_contextual(self):
        # Create convo and mock a Recruiter message asking for availability
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        
        Message.objects.create(
            conversation=convo,
            sender=self.user2,
            content="When are you available for a quick chat?"
        )
        
        self.client.login(username='user1', password='password123')
        response = self.client.get(f'/messages/generate-reply/{convo.id}/')
        
        self.assertEqual(response.status_code, 200)
        reply = response.json()['reply']
        self.assertIn('available this Tuesday or Thursday', reply)

    def test_has_user_sent_context(self):
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        
        self.client.login(username='user1', password='password123')
        
        # 1. No messages yet -> has_user_sent should be False
        response = self.client.get(f'/messages/chat/{convo.id}/')
        self.assertFalse(response.context['has_user_sent'])
        
        # 2. Add message from user 1 -> has_user_sent should be True
        Message.objects.create(conversation=convo, sender=self.user1, content="Hello")
        response = self.client.get(f'/messages/chat/{convo.id}/')
        self.assertTrue(response.context['has_user_sent'])

    def test_notification_signal(self):
        # Create convo and send message
        convo = Conversation.objects.create()
        convo.participants.add(self.user1, self.user2)
        
        # User 1 sends message
        Message.objects.create(conversation=convo, sender=self.user1, content="Ping")
        
        # Check if User 2 got a notification
        note = Notification.objects.filter(user=self.user2).last()
        self.assertIsNotNone(note)
        self.assertIn("New message", note.message)


