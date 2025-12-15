from django.core.management.base import BaseCommand
from django.utils import timezone
from courses.models import Course

class Command(BaseCommand):
    help = 'Deactivates courses that have passed their expiration date'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired_courses = Course.objects.filter(is_active=True, expires_on__lt=today)
        
        count = expired_courses.count()
        if count > 0:
            expired_courses.update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f'Successfully deactivated {count} expired courses.'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired courses found.'))
