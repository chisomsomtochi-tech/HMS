from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointment_list, name="list"),
    path("new/", views.appointment_create, name="create"),
    path("<int:pk>/", views.appointment_detail, name="detail"),
    path("<int:pk>/edit/", views.appointment_edit, name="edit"),
    path("<int:pk>/check-in/", views.appointment_check_in, name="check_in"),
    path("<int:pk>/cancel/", views.appointment_cancel, name="cancel"),
    path("<int:pk>/no-show/", views.appointment_no_show, name="no_show"),
    path("<int:pk>/start-encounter/", views.appointment_start_encounter, name="start_encounter"),
]
