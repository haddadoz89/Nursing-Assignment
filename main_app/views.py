from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    CreateView,
    TemplateView,
    UpdateView,
    DeleteView,
    RedirectView,
    FormView,
    DetailView,
)
from django.urls import reverse_lazy, reverse
from .models import (
    User,
    Shift,
    ShiftType,
    Assignment,
    SubAssignment,
    Clinic,
    EmergencyRole,
)
from .forms import (
    ShiftForm,
    CustomUserCreationForm,
    DateSelectionForm,
    RotationAssignForm,
    ProfileUpdateForm,
)
from django.urls import reverse_lazy
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
import datetime
import calendar

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == "MANAGER"

class DashboardView(LoginRequiredMixin, ListView):
    model = Shift
    template_name = "dashboard.html"
    context_object_name = "shifts"

    def get_queryset(self):
        return Shift.objects.filter(date=datetime.date.today()).select_related(
            "staff", "shift_type"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = datetime.date.today()
        return context

class ShiftCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = "shift_form.html"

    def get_success_url(self):
        shift_date = self.object.date
        return reverse(
            "main_app:monthly_roster",
            kwargs={"year": shift_date.year, "month": shift_date.month},
        )

    def get_initial(self):
        initial = super().get_initial()
        staff_id = self.kwargs.get("staff_id")
        if staff_id:
            initial["staff"] = User.objects.get(pk=staff_id)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "staff_id" in self.kwargs:
            form.fields["staff"].disabled = True
        return form

class ShiftUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Shift
    form_class = ShiftForm
    template_name = "shift_form.html"

    def get_success_url(self):
        shift_date = self.object.date
        return reverse(
            "main_app:monthly_roster",
            kwargs={"year": shift_date.year, "month": shift_date.month},
        )


class ShiftDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Shift
    template_name = "shift_confirm_delete.html"

    def get_success_url(self):
        shift_date = self.object.date
        return reverse(
            "main_app:monthly_roster",
            kwargs={"year": shift_date.year, "month": shift_date.month},
        )


class UserCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "user_form.html"

    def get_success_url(self):
        today = datetime.date.today()
        return reverse(
            "main_app:monthly_roster", kwargs={"year": today.year, "month": today.month}
        )


class IndexRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        today = datetime.date.today()
        return reverse_lazy(
            "main_app:monthly_roster", kwargs={"year": today.year, "month": today.month}
        )


class MonthlyRosterView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.kwargs.get("year", datetime.date.today().year)
        month = self.kwargs.get("month", datetime.date.today().month)
        current_date = datetime.date(year, month, 1)

        context["previous_month"] = current_date - relativedelta(months=1)
        context["next_month"] = current_date + relativedelta(months=1)

        all_staff = User.objects.filter(is_active=True).order_by("first_name")

        shifts_for_month = (
            Shift.objects.filter(date__year=year, date__month=month)
            .select_related("staff", "shift_type")
            .prefetch_related(
                "assignments", "sub_assignments", "clinics", "emergency_roles"
            )
        )

        month_name = calendar.month_name[month]
        num_days = calendar.monthrange(year, month)[1]
        day_headers = range(1, num_days + 1)

        roster_data = []
        for staff_member in all_staff:
            days_data = {day: [] for day in day_headers}

            staff_shifts = shifts_for_month.filter(staff=staff_member)

            for shift in staff_shifts:
                day_number = shift.date.day
                days_data[day_number].append(shift)

            roster_data.append(
                {
                    "staff": staff_member,
                    "days": days_data,
                }
            )

        context["roster_data"] = roster_data
        context["day_headers"] = day_headers
        context["month_name"] = month_name
        context["year"] = year

        return context


class DailyDetailView(LoginRequiredMixin, TemplateView):
    template_name = "daily_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        day = self.kwargs.get("day")

        view_date = datetime.date(year, month, day)
        context["view_date"] = view_date
        shifts = Shift.objects.filter(date=view_date).order_by(
            "shift_type__start_time", "staff__first_name"
        )
        context["nurse_shifts"] = shifts.filter(
            staff__role__in=["NURSE", "MANAGER"])
        context["mas_shifts"] = shifts.filter(staff__role="MAS")

        return context


class MyScheduleView(LoginRequiredMixin, ListView):
    model = Shift
    template_name = "my_schedule.html"
    context_object_name = "my_shifts"

    def get_queryset(self):
        return Shift.objects.filter(
            staff=self.request.user, date__gte=datetime.date.today()
        ).order_by("date", "shift_type__start_time")

class DailyAssignRedirectView(LoginRequiredMixin, ManagerRequiredMixin, FormView):
    template_name = "daily_assign_select_date.html"
    form_class = DateSelectionForm

    def form_valid(self, form):
        date = form.cleaned_data["date"]
        return redirect(
            "main_app:daily_assign", year=date.year, month=date.month, day=date.day
        )

class DailyAssignView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'daily_assign_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        view_date = datetime.date(year, month, day)

        context['view_date'] = view_date
        context['main_assignments'] = Assignment.objects.all()
        context['sub_assignments'] = SubAssignment.objects.all()
        context['clinics'] = Clinic.objects.all()
        context['emergency_roles'] = EmergencyRole.objects.all()

        context['shift_types'] = ShiftType.objects.all()
        context['staff_members'] = User.objects.filter(
            is_active=True).order_by('first_name')

        existing_shifts = Shift.objects.filter(date=view_date).prefetch_related(
            'assignments', 'sub_assignments', 'clinics', 'emergency_roles'
        )
        context['existing_shifts'] = existing_shifts

        return context

    def post(self, request, *args, **kwargs):
        view_date = datetime.date(self.kwargs.get(
            'year'), self.kwargs.get('month'), self.kwargs.get('day'))
        staff_shift_tasks = {}

        for key, staff_id in request.POST.items():
            if key in ['csrfmiddlewaretoken'] or not staff_id:
                continue

            parts = key.split('_')
            task_type = parts[0]
            shift_type_id = int(parts[1])
            task_id = int(parts[2])

            dict_key = (staff_id, shift_type_id)
            if dict_key not in staff_shift_tasks:
                staff_shift_tasks[dict_key] = {
                    'assignments': [], 'sub_assignments': [], 'clinics': [], 'emergency_roles': []
                }

            if task_type == 'main':
                staff_shift_tasks[dict_key]['assignments'].append(task_id)
            elif task_type == 'sub':
                staff_shift_tasks[dict_key]['sub_assignments'].append(task_id)
            elif task_type == 'clinic':
                staff_shift_tasks[dict_key]['clinics'].append(task_id)
            elif task_type == 'emergency':
                staff_shift_tasks[dict_key]['emergency_roles'].append(task_id)

        Shift.objects.filter(date=view_date).delete()

        for (staff_id, shift_type_id), tasks in staff_shift_tasks.items():
            new_shift = Shift.objects.create(
                staff_id=staff_id,
                shift_type_id=shift_type_id,
                date=view_date
            )
            new_shift.assignments.set(tasks['assignments'])
            new_shift.sub_assignments.set(tasks['sub_assignments'])
            new_shift.clinics.set(tasks['clinics'])
            new_shift.emergency_roles.set(tasks['emergency_roles'])

        return redirect('main_app:daily_detail', year=view_date.year, month=view_date.month, day=view_date.day)


class BulkAssignView(LoginRequiredMixin, ManagerRequiredMixin, FormView):
    template_name = "bulk_assign_form.html"
    form_class = RotationAssignForm
    success_url = reverse_lazy("main_app:index")

    def form_valid(self, form):
        employees = form.cleaned_data["employees"]
        rotation = form.cleaned_data["rotation"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        rotation_days = list(rotation.days.all())
        if not rotation_days:
            return super().form_invalid(form)

        for employee in employees:
            Shift.objects.filter(
                staff=employee, date__range=(start_date, end_date)
            ).delete()

            current_date = start_date
            day_counter = 0
            while current_date <= end_date:
                rotation_day = rotation_days[day_counter % len(rotation_days)]

                if not rotation_day.is_day_off:
                    Shift.objects.create(
                        staff=employee,
                        date=current_date,
                        shift_type=rotation_day.shift_type,
                    )

                current_date += datetime.timedelta(days=1)
                day_counter += 1

        return super().form_valid(form)

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset=None):
        # This ensures the user can only see their own profile
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'profile_form.html'
    success_url = reverse_lazy('main_app:profile')

    def get_object(self, queryset=None):
        # This ensures the user can only edit their own profile
        return self.request.user