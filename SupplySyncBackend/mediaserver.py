from django.http import HttpResponse, Http404
from django.conf import settings
import os

def serve_media(request, file_path):
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(full_path):
        with open(full_path, 'rb') as file:
            return HttpResponse(file.read(), content_type='image/png')
    else:
        raise Http404("File not found")
