from django.shortcuts import render


def daily_page(request):
    return render(request, "moon/daily.html")

def visibility_page(request):
    return render(request, "moon/visibility.html")

def login_page(request):
    return render(request, "moon/login.html")

def login_page(request):
    return render(request, "moon/login.html")

def register_page(request):
    return render(request, "moon/register.html")

def favourites_page(request):
    return render(request, "moon/favourites.html")

def observations_page(request):
    return render(request, "moon/observations.html")
