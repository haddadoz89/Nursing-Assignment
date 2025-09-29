# In main_app/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Shift, User, Rotation

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