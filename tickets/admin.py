from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserProfile, UserGroup, Incident, Service

class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        email = cleaned_data.get('email')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')

        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']

        # Generate unique username
        username = f"{first_name.lower().replace(' ', '')}{last_name.lower().replace(' ', '')}"
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{first_name.lower().replace(' ', '')}{last_name.lower().replace(' ', '')}{counter}"
            counter += 1

        user.username = username
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            # Add user to default User group
            user_group, created = Group.objects.get_or_create(name='User')
            user.groups.add(user_group)
            # Create UserProfile
            UserProfile.objects.create(user=user)
        return user

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'password', 'confirm_password'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_department', 'get_phone_number')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') else '-'
    get_department.short_description = 'Department'

    def get_phone_number(self, obj):
        return obj.profile.phone_number if hasattr(obj, 'profile') else '-'
    get_phone_number.short_description = 'Phone Number'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'phone_number', 'user_group')
    search_fields = ('user__username', 'department', 'phone_number')
    list_filter = ('department', 'user_group')

class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    list_filter = ('name',)

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'state', 'reportedby', 'assignee', 'incidentcreated')
    list_filter = ('priority', 'state', 'reportedby', 'assignee')
    search_fields = ('title', 'description')
    date_hierarchy = 'incidentcreated'
    readonly_fields = ('incidentcreated',)

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'last_updated', 'updated_by')
    list_filter = ('status',)
    search_fields = ('name',)

# Unregister the default User admin
admin.site.unregister(User)

# Register the models with custom admin classes
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserGroup, UserGroupAdmin)
admin.site.register(Incident, IncidentAdmin)
admin.site.register(Service, ServiceAdmin)
