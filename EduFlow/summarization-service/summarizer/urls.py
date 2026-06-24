from django.urls import path
from .views import summarize, invalidate_cache

urlpatterns = [
    path("summarize/", summarize, name="summarize"),
    path("cache/<int:article_id>/", invalidate_cache, name="invalidate_cache"),
]
