# In main_app/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Shift, User, Rotation, MonthlyAssignment

class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['staff', 'date', 'shift_type', 'assignments',
                  'sub_assignments', 'clinics', 'emergency_roles', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'assignments': forms.CheckboxSelectMultiple,
            'sub_assignments': forms.CheckboxSelectMultiple,
            'clinics': forms.CheckboxSelectMultiple,
            'emergency_roles': forms.CheckboxSelectMultiple,
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'role', 'phone_number', 'employee_id')

class DateSelectionForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class RotationAssignForm(forms.Form):
    employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    rotation = forms.ModelChoiceField(
        queryset=Rotation.objects.all(),
        required=True
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number','employee_id']

class MonthlyAssignmentForm(forms.ModelForm):
    class Meta:
        model = MonthlyAssignment
        fields = ['staff', 'task', 'start_date', 'end_date', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AppraisalFilterForm(forms.Form):
    staff = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name'),
        label="Select Staff Member",
        required=True
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)