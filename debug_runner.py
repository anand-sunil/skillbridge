import os
import sys
import django
from django.core.management import call_command
import traceback

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillbridge.settings')
django.setup()

try:
    print("Starting test run...")
    call_command('test', 'messaging', verbosity=2, interactive=False)
except Exception:
    print("Exception caught!")
    with open('full_error.log', 'w') as f:
        traceback.print_exc(file=f)
    traceback.print_exc() # also print to stdout
