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
]