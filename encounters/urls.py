from django.urls import path

from . import views

app_name = "encounters"

urlpatterns = [
    path("", views.encounter_list, name="list"),
    path("new/", views.encounter_create, name="create"),
    path("<int:pk>/", views.encounter_detail, name="detail"),
    path("<int:pk>/triage/", views.encounter_triage, name="triage"),
    path("<int:pk>/exam/", views.encounter_exam, name="exam"),
    path("<int:pk>/complete/", views.encounter_complete, name="complete"),
    path("<int:pk>/reopen/", views.encounter_reopen, name="reopen"),
    path("<int:pk>/print/", views.encounter_print, name="print"),
    path("<int:pk>/prescription/print/", views.prescription_print, name="prescription_print"),
]
