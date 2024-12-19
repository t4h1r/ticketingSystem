from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from .models import Incident, Service
from .forms import IncidentForm, UserProfileForm, ServiceStatusForm, ServiceForm
from datetime import datetime
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.urls import reverse  # Import reverse to get URL by name
from django.db.models import Q
import random
from django.utils import timezone
from django.views.decorators.http import require_POST

@login_required
def incident_list(request):
    # Get incidents reported by the user
    reported_incidents = Incident.objects.filter(
        reportedby=request.user.profile
    ).select_related('reportedby__user', 'assignee__user').order_by('-incidentcreated')

    # Get incidents assigned to the user (only for staff/superusers)
    assigned_incidents = None
    if request.user.is_staff or request.user.is_superuser:
        assigned_incidents = Incident.objects.filter(
            assignee=request.user.profile
        ).select_related('reportedby__user', 'assignee__user').order_by('-incidentcreated')

    # If user is staff or superuser, also get all incidents
    all_incidents = None
    if request.user.is_staff or request.user.is_superuser:
        all_incidents = Incident.objects.all().select_related(
            'reportedby__user', 'assignee__user'
        ).order_by('-incidentcreated')

    context = {
        'reported_incidents': reported_incidents,
        'assigned_incidents': assigned_incidents,
        'all_incidents': all_incidents,
        'user_email': request.user.email,
        'is_staff': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, 'tickets/incident_list.html', context)

@login_required
def create_incident(request):
    if request.method == 'POST':
        form = IncidentForm(request.POST, user=request.user)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reportedby = request.user.profile
            
            # Get all staff users (excluding superusers)
            staff_users = User.objects.filter(is_staff=True, is_superuser=False)
            
            # If no staff users found, assign to superusers
            if not staff_users.exists():
                staff_users = User.objects.filter(is_superuser=True)
            
            # If any staff/superusers exist, randomly assign to one of them
            if staff_users.exists():
                random_staff = random.choice(staff_users)
                incident.assignee = random_staff.profile
            else:
                # If no staff/superusers exist, assign to the reporter
                incident.assignee = request.user.profile
            
            incident.state = "New"
            incident.incidentcreated = timezone.now()
            incident.save()
            messages.success(request, 'Incident created successfully.')
            return redirect('incident_list')
        else:
            messages.error(request, 'Please fill in all required fields.')
    else:
        form = IncidentForm(user=request.user)
    
    return render(request, 'tickets/incident_form.html', {
        'form': form,
        'title': 'Create Incident',
        'button_text': 'Create',
        'user_email': request.user.email
    })

# def logout_view(request):
#     logout(request)
#     return render(request, 'registration/logout.html')

# @login_required
# def profile(request):
#     return render(request, 'tickets/profile.html', {'user': request.user})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'registration/profile.html', {
        'form': form,
        'user': request.user
    })

def logout_view(request):
    logout(request)
    return redirect('login')

def generate_unique_username(first_name, last_name):
    # Convert to lowercase and remove spaces
    base_username = f"{first_name.lower().replace(' ', '')}{last_name.lower().replace(' ', '')}"
    username = base_username
    counter = 1
    
    # Keep trying until we find a unique username
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def user_create(request):
    context = {}
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validate passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            context['preview_username'] = generate_unique_username(first_name, last_name)
            return render(request, 'users/user_create.html', context)

        # Check for duplicate email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already registered. Please use a different email.')
            context['preview_username'] = generate_unique_username(first_name, last_name)
            context['email_error'] = True
            return render(request, 'users/user_create.html', context)

        try:
            # Generate unique username
            username = generate_unique_username(first_name, last_name)

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Set default role as 'User' by adding to User group
            user_group, created = Group.objects.get_or_create(name='User')
            user.groups.add(user_group)
            
            messages.success(request, 
                f'User account created successfully! Your username is: <strong>{username}</strong><br>'
                f'Please save this username for login.'
            )
            
            # Redirect to admin dashboard if user is admin, otherwise to incident list
            if request.user.is_authenticated and request.user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('incident_list')

        except ValidationError as e:
            messages.error(request, str(e))
            context['preview_username'] = username
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            if first_name and last_name:
                context['preview_username'] = generate_unique_username(first_name, last_name)

    return render(request, 'users/user_create.html', context)

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'users': User.objects.all(),
        'groups': Group.objects.all(),
    }
    return render(request, 'admin/admin_dashboard.html', context)

@user_passes_test(is_admin)
def admin_create_user(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        is_staff = request.POST.get('is_staff', False) == 'on'
        
        # Validate passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('admin_dashboard')

        # Check for duplicate email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already registered. Please use a different email.')
            return redirect('admin_dashboard')

        try:
            # Generate unique username
            username = generate_unique_username(first_name, last_name)
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff
            )

            # Add user to default User group
            user_group, created = Group.objects.get_or_create(name='User')
            user.groups.add(user_group)
            
            # Create UserProfile
            UserProfile.objects.create(user=user)
            
            messages.success(request, 
                f'User account created successfully! Username: <strong>{username}</strong>'
            )
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def admin_create_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        try:
            Group.objects.create(name=group_name)
            messages.success(request, f'Group {group_name} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating group: {str(e)}')
            
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def admin_assign_group(request):
    if request.method == 'POST':
        user_id = request.POST['user']
        group_id = request.POST['group']
        
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
            messages.success(request, f'User {user.username} added to group {group.name} successfully!')
        except Exception as e:
            messages.error(request, f'Error assigning group: {str(e)}')
            
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_email = request.POST['email']

        # Check for duplicate email only if email is being changed
        if new_email != user.email and User.objects.filter(email=new_email).exists():
            messages.error(request, 'This email address is already in use by another user.')
            return redirect('admin_dashboard')

        try:
            user.email = new_email
            user.is_staff = request.POST.get('is_staff', False) == 'on'
            user.is_active = request.POST.get('is_active', False) == 'on'
            
            # Update groups
            user.groups.clear()
            group_ids = request.POST.getlist('groups')
            for group_id in group_ids:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
                
            user.save()
            messages.success(request, f'User {user.username} updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
            
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            messages.error(request, "Cannot delete superuser!")
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} deleted successfully!')
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def admin_edit_group(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        group.name = request.POST['group_name']
        group.save()
        messages.success(request, f'Group {group.name} updated successfully!')
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def admin_delete_group(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        group_name = group.name
        group.delete()
        messages.success(request, f'Group {group_name} deleted successfully!')
    return redirect('admin_dashboard')

@login_required
def incident_detail(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    return render(request, 'tickets/incident_detail.html', {'incident': incident})

@login_required
def incident_edit(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    
    # Check if the user has permission to edit
    if not (request.user.is_staff or request.user.is_superuser or incident.reportedby.user == request.user):
        messages.error(request, "You don't have permission to edit this incident.")
        return redirect('incident_detail', incident_id=incident_id)
    
    if request.method == 'POST':
        # Update the incident
        incident.title = request.POST['title']
        incident.priority = request.POST['priority']
        incident.state = request.POST['state']
        incident.description = request.POST['description']
        incident.save()
        
        messages.success(request, 'Incident updated successfully.')
        return redirect('incident_detail', incident_id=incident_id)
    
    return render(request, 'tickets/incident_edit.html', {'incident': incident})

@login_required
def incident_delete(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    # Only staff and superusers can delete incidents
    if request.user.is_staff or request.user.is_superuser:
        incident.delete()
        messages.success(request, 'Incident deleted successfully.')
    else:
        messages.error(request, 'Only staff members can delete incidents.')
    return redirect('incident_list')

def preview_username(request):
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    username = generate_unique_username(first_name, last_name)
    return JsonResponse({'username': username})

def index(request):
    if request.user.is_authenticated:
        return redirect('incident_list')
    return render(request, 'tickets/index.html')

class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email or Username'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email or username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = EmailOrUsernameAuthenticationForm
    
    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse('admin_dashboard')
        return reverse('incident_list')
    
    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me', False)
        if not remember_me:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

@login_required
def service_status(request):
    services = Service.objects.all()
    return render(request, 'tickets/service_status.html', {
        'services': services,
        'show_admin_actions': request.user.is_superuser
    })

@login_required
@require_POST
def update_service_status(request, service_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    service = get_object_or_404(Service, id=service_id)
    form = ServiceStatusForm(request.POST, instance=service)
    
    if form.is_valid():
        service = form.save(commit=False)
        service.updated_by = request.user.profile
        service.save()
        return JsonResponse({
            'status': service.status,
            'last_updated': service.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_by': str(service.updated_by)
        })
    
    return JsonResponse({'error': 'Invalid form data'}, status=400)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service created successfully.')
            return redirect('service_status')
    else:
        form = ServiceForm()
    
    return render(request, 'tickets/service_form.html', {
        'form': form,
        'title': 'Create Service',
        'button_text': 'Create'
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully.')
            return redirect('service_status')
    else:
        form = ServiceForm(instance=service)
    
    return render(request, 'tickets/service_form.html', {
        'form': form,
        'title': 'Edit Service',
        'button_text': 'Update'
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    try:
        service.delete()
        messages.success(request, 'Service deleted successfully.')
    except Exception as e:
        messages.error(request, 'Cannot delete this service as it has incidents linked to it.')
    return redirect('service_status')
