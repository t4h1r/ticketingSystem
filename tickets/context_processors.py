from tickets.models import Incident

def incident_counts(request):
    """Add incident counts to the template context for all views."""
    context = {
        'reported_incidents_count': 0,
        'assigned_incidents_count': 0
    }
    
    if request.user.is_authenticated:
        context['reported_incidents_count'] = Incident.objects.filter(
            reportedby=request.user.profile
        ).count()
        context['assigned_incidents_count'] = Incident.objects.filter(
            assignee=request.user.profile
        ).count()
    
    return context
