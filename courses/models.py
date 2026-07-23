from django.db import models
from django.utils.text import slugify
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True,help_text='Unique identifier used in URLs and system queries. Automatically generated if empty.')
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False, help_text='If checked, all logged-in users can access lessons without enrollment or payment.')
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey('category.Category', on_delete=models.SET_NULL, null=True, related_name='courses')
    instructor = models.ForeignKey('instructors.Instructor', on_delete=models.CASCADE, related_name='courses')
    tags = models.ManyToManyField(Tag, related_name='courses', blank=True)

    # new field
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/', 
        blank=True, 
        null=True
    )

    def __str__(self):
        return self.title

    @property
    def approved_reviews(self):
        return self.reviews.filter(is_approved=True).select_related('student__user')

    @property
    def average_rating(self):
        approved = self.reviews.filter(is_approved=True)
        if not approved.exists():
            return 0.0
        total_rating = sum(r.rating for r in approved)
        return round(total_rating / approved.count(), 1)
