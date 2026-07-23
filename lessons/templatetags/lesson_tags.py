# lessons/templatetags/lesson_tags.py
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='youtube_timestamps')
def youtube_timestamps(text):
    if not text:
        return ""
    
    pattern = r'(?:(\d{1,2}):)?(\d{2}):(\d{2})'
    
    def replace_with_link(match):
        hours = match.group(1)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        total_seconds = (int(hours) * 3600 if hours else 0) + (minutes * 60) + seconds
        timestamp_string = match.group(0)
        return f'<a href="#" class="yt-timestamp text-primary fw-bold text-decoration-none" data-seconds="{total_seconds}">{timestamp_string}</a>'
    
    result = re.sub(pattern, replace_with_link, text)
    return mark_safe(result)
