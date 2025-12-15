from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'messaging'

    def ready(self):
        import messaging.signals
