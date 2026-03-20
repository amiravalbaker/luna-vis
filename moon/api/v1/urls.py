from django.urls import path

from .views import (
    daily_view,
    visibility_view,
    visibility_window_view,
    observations_view,
    favourites_view,
    favourite_detail_view,
    register_view,
    me_view,
    location_meta_view,
     send_verification_email_view,
     verify_email_view,
     resend_verification_email_view,
     password_reset_request_view,
     password_reset_confirm_view,
    test_email_view,
)

urlpatterns = [
    path("daily/", daily_view, name="api-daily"),
    path("visibility/", visibility_view, name="api-visibility"),
    path("visibility-window/", visibility_window_view, name="api-visibility-window"),
    path("observations/", observations_view, name="api-observations"),
    path("favourites/", favourites_view, name="api-favourites"),
    path("favourites/<int:pk>/", favourite_detail_view, name="api-favourite-detail"),
    path("register/", register_view, name="api-register"),
    path("me/", me_view, name="api-me"),
    path("location-meta/", location_meta_view, name="api-location-meta"),
     path("auth/send-verification-email/", send_verification_email_view, name="api-send-verification-email"),
     path("auth/verify-email/", verify_email_view, name="api-verify-email"),
     path("auth/resend-verification-email/", resend_verification_email_view, name="api-resend-verification-email"),
     path("auth/password-reset-request/", password_reset_request_view, name="api-password-reset-request"),
     path("auth/password-reset-confirm/", password_reset_confirm_view, name="api-password-reset-confirm"),
    path("auth/test-email/", test_email_view, name="api-test-email"),
]