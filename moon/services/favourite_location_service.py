from moon.models import FavouriteLocation


def create_favourite_location(*, user, name, latitude, longitude, elevation_m=0):
    return FavouriteLocation.objects.create(
        user=user,
        name=name,
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
    )