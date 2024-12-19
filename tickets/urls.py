from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from .views import CustomLoginView

urlpatterns = [
    # Authentication URLs (no login required)
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user/create/', views.user_create, name='user_create'),
    
    # Protected URLs (login required)
    path('', views.index, name='index'),
    path('incidents/', login_required(views.incident_list), name='incident_list'),
    path('profile/', login_required(views.profile), name='profile'),
    path('create/', login_required(views.create_incident), name='create_incident'),
    path('incident/<int:incident_id>/', login_required(views.incident_detail), name='incident_detail'),
    path('incident/<int:incident_id>/edit/', login_required(views.incident_edit), name='incident_edit'),
    path('incident/<int:incident_id>/delete/', login_required(views.incident_delete), name='incident_delete'),
    
    # Admin URLs (superuser required)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-create-user/', views.admin_create_user, name='admin_create_user'),
    path('admin-edit-user/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('admin-delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-create-group/', views.admin_create_group, name='admin_create_group'),
    path('admin-edit-group/<int:group_id>/', views.admin_edit_group, name='admin_edit_group'),
    path('admin-delete-group/<int:group_id>/', views.admin_delete_group, name='admin_delete_group'),
    path('preview-username/', views.preview_username, name='preview_username'),
    
    # Service Status URLs
    path('services/', views.service_status, name='service_status'),
    path('services/create/', views.create_service, name='create_service'),
    path('services/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('services/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('service/<int:service_id>/update-status/', views.update_service_status, name='update_service_status'),
]