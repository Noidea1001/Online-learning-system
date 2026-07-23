import re
from django.db import models
class Lesson(models.Model):
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    video_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="YouTube URL (any format) or direct video link"
    )
    video_file = models.FileField(
        upload_to='lessons/videos/', 
        blank=True, 
        null=True,
        help_text="Upload MP4 video file (alternative to YouTube)"
    )
    
    pdf_resource = models.FileField(
        upload_to='lessons/documents/', 
        blank=True, 
        null=True,
        help_text="Optional PDF materials"
    )

    class Meta:
        ordering = ['order']
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        

    def save(self, *args, **kwargs):
        if not self.pk:
            last_lesson = Lesson.objects.filter(course=self.course).order_by('-order').first()
            if last_lesson:
                self.order = last_lesson.order + 1
            else:
                self.order = 1
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} - {self.title}"

# ==================== YouTube Helpers =========
    @property
    def youtube_video_id(self) -> str:
        """Extract YouTube video ID from various URL formats."""
        if not self.video_url:
            return ""

        url = self.video_url.strip()
    
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url

        return ""

    @property
    def youtube_embed_url(self) -> str | None:
        video_id = self.youtube_video_id
        if not video_id:
            return None

        return (
            f"https://www.youtube.com/embed/{video_id}?"
            "enablejsapi=1&rel=0&modestbranding=1&showinfo=0&fs=1"
        )


    @property
    def has_video(self) -> bool:
        return bool(self.youtube_video_id or self.video_file)

    @property
    def video_type(self) -> str:
        if self.youtube_video_id:
            return "youtube"
        elif self.video_file:
            return "file"
        return "none"