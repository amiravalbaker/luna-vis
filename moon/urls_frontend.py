from django.urls import path
from .views_frontend import (
    daily_page,
    visibility_page,
    login_page,
    register_page,
    verify_email_page,
    reset_password_page,
    favourites_page,
    observations_page,
)

urlpatterns = [
    path("", daily_page, name="daily-page"),
    path("visibility/", visibility_page, name="visibility-page"),
    path("login/", login_page, name="login-page"),
    path("register/", register_page, name="register-page"),
    path("verify-email/", verify_email_page, name="verify-email-page"),
    path("reset-password/", reset_password_page, name="reset-password-page"),
    path("favourites/", favourites_page, name="favourites-page"),
    path("observations/", observations_page, name="observations-page"),
]