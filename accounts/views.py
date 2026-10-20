from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, FormView, ListView, UpdateView

from .forms import (
    StaffCreateForm,
    StaffEditForm,
    StaffPasswordResetForm,
    StyledPasswordChangeForm,
)
from .models import Role, User
from .permissions import CapabilityRequiredMixin, capability_required


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.display_name}.")
        return response


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("accounts:login")


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("core:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        messages.success(self.request, "Your password has been updated.")
        return response


class StaffListView(CapabilityRequiredMixin, ListView):
    required_capabilities = ("manage_staff",)
    model = User
    template_name = "accounts/staff_list.html"
    context_object_name = "staff"
    paginate_by = 30

    def get_queryset(self):
        return User.objects.order_by("-is_active", "first_name", "last_name", "username")


class StaffDetailView(CapabilityRequiredMixin, DetailView):
    required_capabilities = ("manage_staff",)
    model = User
    template_name = "accounts/staff_detail.html"
    context_object_name = "member"


class StaffCreateView(CapabilityRequiredMixin, FormView):
    required_capabilities = ("manage_staff",)
    form_class = StaffCreateForm
    template_name = "accounts/staff_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context

    def form_valid(self, form):
        user = form.save()
        messages.success(
            self.request,
            f"Account created for {user.display_name}. Share the temporary password "
            "securely; they will be asked to change it at first sign-in.",
        )
        return redirect("accounts:staff_detail", pk=user.pk)


class StaffUpdateView(CapabilityRequiredMixin, UpdateView):
    required_capabilities = ("manage_staff",)
    model = User
    form_class = StaffEditForm
    template_name = "accounts/staff_form.html"
    context_object_name = "member"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        return context

    def form_valid(self, form):
        target = self.object
        new_role = form.cleaned_data["role"]

        if target.pk == self.request.user.pk and new_role != Role.ADMIN:
            form.add_error("role", "You cannot remove your own administrator role.")
            return self.form_invalid(form)

        if (
            target.role == Role.ADMIN
            and new_role != Role.ADMIN
            and target.is_active
            and User.objects.filter(role=Role.ADMIN, is_active=True).count() <= 1
        ):
            form.add_error("role", "At least one active administrator is required.")
            return self.form_invalid(form)

        messages.success(self.request, f"{form.save().display_name}'s account was updated.")
        return redirect("accounts:staff_detail", pk=target.pk)


class StaffPasswordResetView(CapabilityRequiredMixin, FormView):
    required_capabilities = ("manage_staff",)
    form_class = StaffPasswordResetForm
    template_name = "accounts/staff_password_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.target_user = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.target_user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member"] = self.target_user
        return context

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f"Password reset for {self.target_user.display_name}. They must change it "
            "at next sign-in.",
        )
        return redirect("accounts:staff_detail", pk=self.target_user.pk)


@capability_required("manage_staff")
@require_POST
def staff_toggle_active(request, pk):
    target = get_object_or_404(User, pk=pk)

    if target.pk == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("accounts:staff_detail", pk=pk)

    if (
        target.is_active
        and target.role == Role.ADMIN
        and User.objects.filter(role=Role.ADMIN, is_active=True).count() <= 1
    ):
        messages.error(request, "At least one active administrator is required.")
        return redirect("accounts:staff_detail", pk=pk)

    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    state = "reactivated" if target.is_active else "deactivated"
    messages.success(request, f"{target.display_name} was {state}.")
    return redirect("accounts:staff_detail", pk=pk)
