# online_learning_system/views.py
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import render


def offline(request):
    """Standalone, dependency-free fallback page the service worker serves
    when a navigation request fails while offline."""
    return render(request, 'offline.html')


def service_worker(request):
    """
    Serves the service worker from the site root (/sw.js) rather than from
    /static/pwa/sw.js. A service worker's control scope defaults to the
    directory it's served from, so serving it from /static/ would limit it
    to only ever controlling /static/* requests. Serving it from the root
    URL gives it the whole site by default, with no extra headers needed.
    """
    sw_path = finders.find('pwa/sw.js')
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')
