from django.core.management.base import BaseCommand
from tickets.models import Service

class Command(BaseCommand):
    help = 'Adds initial services to the database'

    def handle(self, *args, **kwargs):
        services = [
            'Email System',
            'Network Infrastructure',
            'Database Services',
            'Web Applications',
            'File Storage',
            'Authentication System',
            'Backup Services',
            'Print Services',
            'VPN Access',
            'Internal Communications'
        ]

        created_count = 0
        existing_count = 0

        for service_name in services:
            service, created = Service.objects.get_or_create(
                name=service_name,
                defaults={'status': 'Running'}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created service: {service_name}'))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f'Service already exists: {service_name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nCreated {created_count} new services, {existing_count} already existed.'))
