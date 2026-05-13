from django.contrib import admin

from moon.models import (
	EmailVerificationToken,
	FavouriteLocation,
	Observation,
	ObservationPrediction,
	ObservationSnapshot,
	PasswordResetToken,
	UserProfile,
)


class ObservationSnapshotInline(admin.StackedInline):
	model = ObservationSnapshot
	extra = 0
	can_delete = False


class ObservationPredictionInline(admin.TabularInline):
	model = ObservationPrediction
	extra = 0
	can_delete = False
	fields = ("model_name", "verdict", "band", "score", "created_at")
	readonly_fields = fields


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"user",
		"observer_name",
		"observation_time",
		"visible",
		"detection_method",
		"created_at",
	)
	list_filter = ("visible", "detection_method", "sky_condition", "created_at")
	search_fields = ("observer_name", "notes", "user__username")
	date_hierarchy = "observation_time"
	inlines = (ObservationSnapshotInline, ObservationPredictionInline)


@admin.register(ObservationSnapshot)
class ObservationSnapshotAdmin(admin.ModelAdmin):
	list_display = ("id", "observation", "created_at")
	search_fields = ("observation__observer_name", "observation__user__username")


@admin.register(ObservationPrediction)
class ObservationPredictionAdmin(admin.ModelAdmin):
	list_display = ("id", "observation", "model_name", "verdict", "band", "score", "created_at")
	list_filter = ("model_name", "verdict", "band", "created_at")
	search_fields = ("observation__observer_name", "observation__user__username")


@admin.register(FavouriteLocation)
class FavouriteLocationAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "name", "latitude", "longitude", "elevation_m", "created_at")
	search_fields = ("name", "user__username")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "email_verified", "created_at")
	search_fields = ("user__username", "user__email")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "token", "created_at")
	search_fields = ("user__username", "token")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "token", "created_at")
	search_fields = ("user__username", "token")
