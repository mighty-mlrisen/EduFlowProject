import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .text_cleaner import clean_markdown
from .model_client import call_model_service
from .cache import get_cached_summary, set_cached_summary, delete_cached_summary
from .article_client import fetch_article_text


@csrf_exempt
@require_POST
def summarize(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    article_id = body.get("article_id")
    if article_id is None:
        return JsonResponse({"error": "Field 'article_id' is required"}, status=400)

    cached = get_cached_summary(article_id)
    if cached is not None:
        return JsonResponse({"summary": cached, "cached": True})

    try:
        text = fetch_article_text(article_id)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=502)

    clean_text = clean_markdown(text)
    if not clean_text:
        return JsonResponse({"error": "No text left after cleaning"}, status=400)

    try:
        summary = call_model_service(clean_text)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=502)

    set_cached_summary(article_id, summary)
    return JsonResponse({"summary": summary, "cached": False})


@csrf_exempt
@require_http_methods(["DELETE"])
def invalidate_cache(request, article_id):
    deleted = delete_cached_summary(article_id)
    return JsonResponse({"deleted": deleted})
