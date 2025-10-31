from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
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
    AssignmentGroup,
    AssignmentStatus,
    Committee,
    User,
    Shift,
    ShiftType,
    Assignment,
    SubAssignment,
    Clinic,
    EmergencyRole,
    MonthlyAssignment,
    MonthlyTask,
)
from .forms import (
    ShiftForm,
    CustomUserCreationForm,
    DateSelectionForm,
    RotationAssignForm,
    ProfileUpdateForm,
    MonthlyAssignmentForm,
    AppraisalFilterForm,
    StaffUpdateForm,
)
from django.urls import reverse_lazy
from dateutil.relativedelta import relativedelta
from django.shortcuts import redirect
import datetime
import calendar
from io import BytesIO
from django.http import HttpResponse
from xhtml2pdf import pisa
from collections import Counter


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

class StaffListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = 'staff_list.html'
    context_object_name = 'staff_members'
    ordering = ['first_name']
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True).order_by('first_name')
        return queryset

class StaffDetailView(LoginRequiredMixin, ManagerRequiredMixin, DetailView):
    model = User
    template_name = 'staff_detail.html'
    context_object_name = 'staff_member'

class StaffUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = User
    form_class = StaffUpdateForm
    template_name = 'staff_form.html'

    def get_success_url(self):
        return reverse(
            'main_app:staff_detail',
            kwargs={'pk': self.object.pk}
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
        _, last_day = calendar.monthrange(year, month)
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, last_day)
        context['monthly_assignments'] = MonthlyAssignment.objects.filter(
            start_date__lte=month_end,
            end_date__gte=month_start
        ).select_related('staff', 'task').order_by('task__name')
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

        all_shifts_for_day = Shift.objects.filter(date=view_date).select_related(
            "staff", "shift_type"
        ).prefetch_related(
            "assignments", "sub_assignments", "clinics", "emergency_roles"
        )
    
        shift_types = ShiftType.objects.order_by('start_time')

        shifts_by_type = {}
        for shift_type in shift_types:
            shifts_in_group = all_shifts_for_day.filter(shift_type=shift_type)
            
            shifts_by_type[shift_type.name] = {
                'nurse_shifts': shifts_in_group.filter(staff__role__in=['NURSE', 'MANAGER']),
                'mas_shifts': shifts_in_group.filter(staff__role='MAS')
            }
        
        context['shifts_by_type'] = shifts_by_type
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
    template_name = "daily_assign_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        day = self.kwargs.get("day")
        view_date = datetime.date(year, month, day)

        context["view_date"] = view_date
        start_date = view_date - datetime.timedelta(days=5)
        recent_shifts = Shift.objects.filter(
            date__range=(start_date, view_date - datetime.timedelta(days=1))
        )

        history = {}
        for shift in recent_shifts:
            staff_id_str = str(shift.staff_id)
            if staff_id_str not in history:
                history[staff_id_str] = {
                    "main": {},
                    "sub": {},
                    "clinic": {},
                    "emergency": {},
                }

            for task in shift.assignments.all():
                history[staff_id_str]["main"][str(task.id)] = shift.date.isoformat()
            for task in shift.sub_assignments.all():
                history[staff_id_str]["sub"][str(task.id)] = shift.date.isoformat()
            for task in shift.clinics.all():
                history[staff_id_str]["clinic"][str(task.id)] = shift.date.isoformat()
            for task in shift.emergency_roles.all():
                history[staff_id_str]["emergency"][
                    str(task.id)
                ] = shift.date.isoformat()

        context["history_json"] = json.dumps(history)

        context["main_assignments"] = Assignment.objects.all()
        context["sub_assignments"] = SubAssignment.objects.all()
        context["clinics"] = Clinic.objects.all()
        context["emergency_roles"] = EmergencyRole.objects.all()

        context["shift_types"] = ShiftType.objects.all()
        context["staff_members"] = User.objects.filter(is_active=True).order_by(
            "first_name"
        )

        existing_shifts = Shift.objects.filter(date=view_date).prefetch_related(
            "assignments", "sub_assignments", "clinics", "emergency_roles"
        )
        context["existing_shifts"] = existing_shifts

        return context

    def post(self, request, *args, **kwargs):
        view_date = datetime.date(
            self.kwargs.get("year"), self.kwargs.get("month"), self.kwargs.get("day")
        )
        staff_shift_tasks = {}

        for key, staff_id in request.POST.items():
            if key in ["csrfmiddlewaretoken"] or not staff_id:
                continue

            parts = key.split("_")
            task_type = parts[0]
            shift_type_id = int(parts[1])
            task_id = int(parts[2])

            dict_key = (staff_id, shift_type_id)
            if dict_key not in staff_shift_tasks:
                staff_shift_tasks[dict_key] = {
                    "assignments": [],
                    "sub_assignments": [],
                    "clinics": [],
                    "emergency_roles": [],
                }

            if task_type == "main":
                staff_shift_tasks[dict_key]["assignments"].append(task_id)
            elif task_type == "sub":
                staff_shift_tasks[dict_key]["sub_assignments"].append(task_id)
            elif task_type == "clinic":
                staff_shift_tasks[dict_key]["clinics"].append(task_id)
            elif task_type == "emergency":
                staff_shift_tasks[dict_key]["emergency_roles"].append(task_id)

        Shift.objects.filter(date=view_date).delete()

        for (staff_id, shift_type_id), tasks in staff_shift_tasks.items():
            new_shift = Shift.objects.create(
                staff_id=staff_id, shift_type_id=shift_type_id, date=view_date
            )
            new_shift.assignments.set(tasks["assignments"])
            new_shift.sub_assignments.set(tasks["sub_assignments"])
            new_shift.clinics.set(tasks["clinics"])
            new_shift.emergency_roles.set(tasks["emergency_roles"])

        return redirect(
            "main_app:daily_detail",
            year=view_date.year,
            month=view_date.month,
            day=view_date.day,
        )


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
    template_name = "profile.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = "profile_form.html"
    success_url = reverse_lazy("main_app:profile")

    def get_object(self, queryset=None):
        return self.request.user


from django.http import HttpRequest


@login_required
def daily_schedule_pdf_view(request: HttpRequest, year: int, month: int, day: int):
    view_date = datetime.date(year, month, day)
    shifts = (
        Shift.objects.filter(date=view_date)
        .select_related("staff", "shift_type")
        .order_by("shift_type__start_time", "staff__first_name")
    )

    shifts_by_type = {}
    for shift in shifts:
        shift_type_name = shift.shift_type.name
        if shift_type_name not in shifts_by_type:
            shifts_by_type[shift_type_name] = {
                "shift_type": shift.shift_type,
                "nurse_shifts": [],
                "mas_shifts": [],
            }

        if shift.staff.role in ["NURSE", "MANAGER"]:
            shifts_by_type[shift_type_name]["nurse_shifts"].append(shift)
        elif shift.staff.role == "MAS":
            shifts_by_type[shift_type_name]["mas_shifts"].append(shift)

    context: dict[str, object] = {
        "view_date": view_date,
        "shifts_by_type": shifts_by_type,
        "is_for_pdf": True,
    }

    html_string = render_to_string("daily_detail.html", context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="daily_schedule_{view_date}.pdf"'
        )
        return response

    return HttpResponse("Error Rendering PDF", status=400)


class StaffAnalyticsView(LoginRequiredMixin, ManagerRequiredMixin, DetailView):
    model = User
    template_name = "staff_analytics.html"
    context_object_name = "staff_member"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        staff_member = self.get_object()

        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        current_date = datetime.date(year, month, 1)

        context["previous_month"] = current_date - relativedelta(months=1)
        context["next_month"] = current_date + relativedelta(months=1)
        context["month_name"] = calendar.month_name[month]
        context["year"] = year

        shifts = Shift.objects.filter(
            staff=staff_member, date__year=year, date__month=month
        ).order_by("date")

        context["shift_history"] = shifts

        monthly_assignments = MonthlyAssignment.objects.filter(
            staff=staff_member, 
            start_date__year=year, 
            start_date__month=month
        ).select_related('task')

        shift_type_counts = Counter()
        assignment_counts = Counter()
        sub_assignment_counts = Counter()
        clinic_counts = Counter()
        emergency_role_counts = Counter()
        monthly_task_counts = Counter(ma.task.name for ma in monthly_assignments)
        

        for shift in shifts:
            shift_type_counts[shift.shift_type.name] += 1
            for assignment in shift.assignments.all():
                assignment_counts[assignment.name] += 1
            for sub_assignment in shift.sub_assignments.all():
                sub_assignment_counts[sub_assignment.name] += 1
            for clinic in shift.clinics.all():
                clinic_counts[clinic.name] += 1
            for emergency_role in shift.emergency_roles.all():
                emergency_role_counts[emergency_role.name] += 1

        context["shift_type_counts"] = dict(shift_type_counts)
        context["assignment_counts"] = dict(assignment_counts)
        context["sub_assignment_counts"] = dict(sub_assignment_counts)
        context["clinic_counts"] = dict(clinic_counts)
        context["emergency_role_counts"] = dict(emergency_role_counts)
        context['monthly_task_counts'] = dict(monthly_task_counts)

        chart_labels = list(shift_type_counts.keys())
        chart_data = list(shift_type_counts.values())

        context["chart_labels_json"] = json.dumps(chart_labels)
        context["chart_data_json"] = json.dumps(chart_data)

        return context
class MonthlyAssignmentListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = MonthlyAssignment
    template_name = 'monthlyassignment_list.html'
    context_object_name = 'assignments'
    ordering = ['-start_date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()
        context['year'] = today.year
        context['month'] = today.month
        return context

class MonthlyAssignmentDisplayView(LoginRequiredMixin, TemplateView):
    template_name = 'monthly_assignment_display.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year', datetime.date.today().year)
        month = self.kwargs.get('month', datetime.date.today().month)
        context['month_name'] = calendar.month_name[month]
        context['year'] = year

        current_date = datetime.date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, last_day)
        context['previous_month'] = current_date - relativedelta(months=1)
        context['next_month'] = current_date + relativedelta(months=1)

        monthly_assignments = MonthlyAssignment.objects.filter(
            start_date__lte=month_end,
            end_date__gte=month_start
        ).select_related('staff', 'task').order_by('task__name')

        context['monthly_assignments'] = monthly_assignments
        return context

class MonthlyAssignmentTodayRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        today = datetime.date.today()
        return reverse_lazy('main_app:monthly_assignment_display', kwargs={'year': today.year, 'month': today.month})

class MonthlyAssignmentBulkAssignView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'monthly_assignment_bulk_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        _, last_day = calendar.monthrange(year, month)
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, last_day)

        context['view_date'] = month_start
        context['month_name'] = calendar.month_name[month]
        context['year'] = year
        
        groups = AssignmentGroup.objects.prefetch_related('staff_members').order_by('name')
        
        context['all_tasks'] = MonthlyTask.objects.all().order_by('name')
        context['all_committees'] = Committee.objects.all().order_by('name')
        
        existing_assignments = MonthlyAssignment.objects.filter(
            start_date=month_start, end_date=month_end
        ).select_related('task', 'committee')
        
        assignment_map = {}
        for assign in existing_assignments:
            if assign.staff_id not in assignment_map:
                assignment_map[assign.staff_id] = {'tasks': [], 'committees': []}
            assignment_map[assign.staff_id]['tasks'].append(assign.task_id)
            if assign.committee_id:
                assignment_map[assign.staff_id]['committees'].append(assign.committee_id)
        
        context['assignment_map'] = assignment_map
        context['groups'] = groups
        return context

    def post(self, request, *args, **kwargs):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        _, last_day = calendar.monthrange(year, month)
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, last_day)

        MonthlyAssignment.objects.filter(start_date=month_start, end_date=month_end).delete()

        all_staff = User.objects.filter(is_active=True)
        for staff in all_staff:
            task_ids = request.POST.getlist(f'tasks_{staff.id}')
            committee_ids = request.POST.getlist(f'committees_{staff.id}')

            group_id = request.POST.get(f'group_{staff.id}')

            if not task_ids and not committee_ids:
                continue

            if not task_ids:
                MonthlyAssignment.objects.create(
                    staff=staff,
                    task=None,
                    start_date=month_start,
                    end_date=month_end,
                    group_id=group_id if group_id else None,
                    committee_id=committee_ids[0] if committee_ids else None
                )
            else:
                for task_id in task_ids:
                    MonthlyAssignment.objects.create(
                        staff=staff,
                        task_id=task_id,
                        start_date=month_start,
                        end_date=month_end,
                        group_id=group_id if group_id else None,
                        committee_id=committee_ids[0] if committee_ids else None,
                        status=AssignmentStatus.PENDING
                    )
        
        messages.success(request, f"Monthly assignments for {calendar.month_name[month]} {year} saved.")
        return redirect('main_app:monthly_assignment_display', year=year, month=month)

class MonthlyAssignmentCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = MonthlyAssignment
    form_class = MonthlyAssignmentForm
    template_name = 'monthlyassignment_form.html'
    success_url = reverse_lazy('main_app:monthly_assignment_list')

class MonthlyAssignmentUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = MonthlyAssignment
    form_class = MonthlyAssignmentForm
    template_name = 'monthlyassignment_form.html'
    success_url = reverse_lazy('main_app:monthly_assignment_list')

class MonthlyAssignmentDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = MonthlyAssignment
    template_name = 'monthlyassignment_confirm_delete.html'
    success_url = reverse_lazy('main_app:monthly_assignment_list')

class ChecklistView(LoginRequiredMixin, TemplateView):
    template_name = 'checklist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()
        team_leader = self.request.user

        leader_shifts = Shift.objects.filter(staff=team_leader, date=today, assignments__name__icontains='Team Leader')

        shifts_to_assess = Shift.objects.none()

        if leader_shifts.exists():
            leader_shift_type = leader_shifts.first().shift_type
            shifts_to_assess = Shift.objects.filter(
                date=today,
                shift_type=leader_shift_type
            ).exclude(staff=team_leader).select_related('staff')

        context['shifts_to_assess'] = shifts_to_assess
        context['is_team_leader_today'] = leader_shifts.exists()
        return context

    def post(self, request, *args, **kwargs):
        for key, value in request.POST.items():
            if key.startswith('status_'):
                shift_id = key.split('_')[1]
                shift = Shift.objects.get(id=shift_id)
                shift.status = value
                shift.team_leader_notes = request.POST.get(f'notes_{shift_id}', '')
                shift.save()

        messages.success(request, "Checklist saved successfully!")
        return redirect('main_app:checklist')

class ManagerReviewView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'manager_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_str = self.request.GET.get('date')
        view_date = None
        
        if date_str:
            try:
                view_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                shifts_for_day = Shift.objects.filter(date=view_date).select_related('staff', 'shift_type')
                context['shifts_for_day'] = shifts_for_day
            except (ValueError, TypeError):
                pass

        context['view_date'] = view_date
        return context

    def post(self, request, *args, **kwargs):
        date_str = request.POST.get('date')
        if not date_str:
            return redirect('main_app:manager_review')

        view_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

        for key, value in request.POST.items():
            if key.startswith('status_'):
                shift_id = key.split('_')[1]
                shift = Shift.objects.get(id=shift_id)
                shift.status = value
                shift.team_leader_notes = request.POST.get(f'notes_{shift_id}', '')
                
                if f'approve_{shift_id}' in request.POST:
                    shift.is_approved_by_manager = True
                
                shift.save()
        
        messages.success(request, f"Checklist for {view_date} has been updated and approved.")
        return redirect(f"{reverse('main_app:manager_review')}?date={date_str}")

class AppraisalAnalyticsView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'appraisal_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = AppraisalFilterForm(self.request.GET or None)
        context['form'] = form

        if form.is_valid():
            staff = form.cleaned_data['staff']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            context['selected_staff'] = staff
            context['date_range'] = (start_date, end_date)

            daily_shifts = Shift.objects.filter(
                staff=staff,
                date__range=(start_date, end_date),
                status__in=['COMPLETED', 'PARTIAL', 'NOT_COMPLETED']
            )
            daily_status_counts = Counter(s.status for s in daily_shifts)
            
            total_daily = daily_shifts.count()
            completed_daily = daily_status_counts.get('COMPLETED', 0)
            daily_completion_percent = (completed_daily / total_daily * 100) if total_daily > 0 else 0
            
            context['daily_completion_percent'] = round(daily_completion_percent, 1)
            context['daily_chart_labels'] = json.dumps(list(daily_status_counts.keys()))
            context['daily_chart_data'] = json.dumps(list(daily_status_counts.values()))

            monthly_assignments = MonthlyAssignment.objects.filter(
                staff=staff,
                end_date__gte=start_date,
                start_date__lte=end_date,
                status__in=['COMPLETED', 'PARTIAL', 'NOT_COMPLETED']
            )
            monthly_status_counts = Counter(ma.status for ma in monthly_assignments)

            total_monthly = monthly_assignments.count()
            completed_monthly = monthly_status_counts.get('COMPLETED', 0)
            monthly_completion_percent = (completed_monthly / total_monthly * 100) if total_monthly > 0 else 0

            context['monthly_completion_percent'] = round(monthly_completion_percent, 1)
            context['monthly_chart_labels'] = json.dumps(list(monthly_status_counts.keys()))
            context['monthly_chart_data'] = json.dumps(list(monthly_status_counts.values()))

        return context