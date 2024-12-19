from django.core.management.base import BaseCommand
from tickets.models import Incident
from django.utils import timezone

class Command(BaseCommand):
    help = 'Lists all incidents in the database'

    def handle(self, *args, **options):
        incidents = Incident.objects.all().select_related('reportedby__user', 'assignee__user')
        
        if not incidents:
            self.stdout.write(self.style.WARNING('No incidents found in the database.'))
            return

        self.stdout.write(self.style.SUCCESS('\nAll Incidents in Database:'))
        self.stdout.write('=' * 100)
        
        for incident in incidents:
            self.stdout.write(self.style.SUCCESS(f'\nIncident #{incident.id}'))
            self.stdout.write('-' * 50)
            self.stdout.write(f'Title: {incident.title}')
            self.stdout.write(f'Status: {incident.state}')
            self.stdout.write(f'Priority: {incident.priority}')
            self.stdout.write(f'Reported By: {incident.reportedby.user.username if incident.reportedby else "N/A"}')
            self.stdout.write(f'Assigned To: {incident.assignee.user.username if incident.assignee else "N/A"}')
            self.stdout.write(f'Created: {incident.incidentcreated.strftime("%Y-%m-%d %H:%M:%S") if incident.incidentcreated else "N/A"}')
            self.stdout.write(f'Description: {incident.description}')
            
        self.stdout.write('\n' + '=' * 100)
