from django.shortcuts import render


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
