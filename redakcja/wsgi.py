import os
import os.path
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add apps and lib directories to PYTHONPATH
sys.path = [
    ROOT,
    os.path.join(ROOT, 'apps'),
    os.path.join(ROOT, 'lib'),
    os.path.join(ROOT, 'lib/librarian'),
] + sys.path


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redakcja.localsettings")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
