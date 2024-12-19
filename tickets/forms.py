from django import forms
from .models import Incident, UserProfile, UserGroup, Service
from django.contrib.auth.models import User

class IncidentForm(forms.ModelForm):
    priority = forms.ChoiceField(
        choices=[('', '---------'), ('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Incident
        fields = ['title', 'assignee', 'affected_service', 'incidentstart', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'affected_service': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'incidentstart': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'required': True
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['assignee'].initial = user.profile
            self.fields['assignee'].widget = forms.HiddenInput()

        # Add empty choice to services
        self.fields['affected_service'].empty_label = "Select a service"
        
        # Make all fields required
        for field_name, field in self.fields.items():
            field.required = True
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' required'
            else:
                field.widget.attrs['class'] = 'required'

    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure all required fields are provided
        required_fields = ['title', 'affected_service', 'incidentstart', 'description', 'priority']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'This field is required.')
        
        return cleaned_data

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }, choices=[
                ('Operational', 'Operational'),
                ('Degraded Performance', 'Degraded Performance'),
                ('Partial Outage', 'Partial Outage'),
                ('Major Outage', 'Major Outage')
            ])
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in self.Meta.fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'This field is required.')
        return cleaned_data

class ServiceStatusForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'location']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }