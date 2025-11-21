from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    body = models.TextField()
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base_slug = slugify(self.title)[:200]
            slug_candidate = base_slug
            counter = 1
            while Post.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"


class PostVisit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_visits')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='visits')
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visited_at']

    def __str__(self):
        return f"{self.user} visited {self.post} at {self.visited_at}"

# Create your models here.
