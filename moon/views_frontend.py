from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


def _assetlinks_file_path() -> Path:
    return Path(__file__).resolve().parent / "static" / ".well-known" / "assetlinks.json"


def daily_page(request):
    return render(request, "moon/daily.html")

def visibility_page(request):
    return render(request, "moon/visibility.html")

def login_page(request):
    return render(request, "moon/login.html")

def register_page(request):
    return render(request, "moon/register.html")

def verify_email_page(request):
    return render(request, "moon/verify_email.html")

def reset_password_page(request):
    return render(request, "moon/reset_password.html")

def favourites_page(request):
    return render(request, "moon/favourites.html")

def observations_page(request):
    return render(request, "moon/observations.html")

def about_page(request):
    return render(request, "moon/about.html")


def assetlinks_json(request):
    file_path = _assetlinks_file_path()
    return HttpResponse(
        file_path.read_text(encoding="utf-8"),
        content_type="application/json",
    )
