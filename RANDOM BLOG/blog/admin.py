from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "created_at")
    list_filter = ("published", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")

# Register your models here.
