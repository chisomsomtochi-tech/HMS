from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("account/password/", views.PasswordChangeView.as_view(), name="password_change"),
    path("staff/", views.StaffListView.as_view(), name="staff_list"),
    path("staff/new/", views.StaffCreateView.as_view(), name="staff_create"),
    path("staff/<int:pk>/", views.StaffDetailView.as_view(), name="staff_detail"),
    path("staff/<int:pk>/edit/", views.StaffUpdateView.as_view(), name="staff_edit"),
    path("staff/<int:pk>/password/", views.StaffPasswordResetView.as_view(), name="staff_password"),
    path("staff/<int:pk>/toggle/", views.staff_toggle_active, name="staff_toggle"),
]
