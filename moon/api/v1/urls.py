from django.urls import path
from .views import daily_view, visibility_view, visibility_window_view, observations_view

urlpatterns = [
    path("daily/", daily_view, name="api-daily"),
    path("visibility/", visibility_view, name="api-visibility"),
    path("visibility-window/", visibility_window_view, name="api-visibility-window"),
    path("observations/", observations_view, name="api-observations"),
]