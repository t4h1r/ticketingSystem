from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from .models import Incident, UserProfile, Service, UserGroup

class IncidentTestCase(TestCase):
    def setUp(self):
        # Create user groups
        self.django_group = Group.objects.create(name='User')
        self.user_group = UserGroup.objects.create(name='User Group')
        
        # Create test users - UserProfile will be created automatically via signal
        self.normal_user = User.objects.create_user(
            username='normal_user',
            email='normal@example.com',
            password='testpass123'
        )
        self.normal_user.groups.add(self.django_group)
        self.normal_user.profile.user_group = self.user_group
        self.normal_user.profile.save()

        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.staff_user.groups.add(self.django_group)
        self.staff_user.profile.user_group = self.user_group
        self.staff_user.profile.save()

        # Create test service
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            status='Operational'
        )

        # Create test incident
        self.incident = Incident.objects.create(
            title='Test Incident',
            description='Test Description',
            priority='High',
            state='New',
            reportedby=self.normal_user.profile,
            assignee=self.staff_user.profile,
            affected_service=self.service,
            incidentcreated=timezone.now(),
            incidentstart=timezone.now()
        )

        # Initialize the test client
        self.client = Client()

    def test_incident_list_view(self):
        # Test unauthenticated access
        response = self.client.get(reverse('incident_list'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        # Test normal user access
        self.client.login(username='normal_user', password='testpass123')
        response = self.client.get(reverse('incident_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/incident_list.html')
        self.assertTrue('reported_incidents' in response.context)

        # Test staff user access
        self.client.login(username='staff_user', password='testpass123')
        response = self.client.get(reverse('incident_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('all_incidents' in response.context)
        self.assertTrue('assigned_incidents' in response.context)

    def test_incident_creation(self):
        self.client.login(username='normal_user', password='testpass123')
        
        # Test incident creation
        incident_data = {
            'title': 'New Test Incident',
            'description': 'New Test Description',
            'priority': 'High',  
            'affected_service': self.service.id,
            'incidentstart': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'assignee': self.normal_user.profile.id  
        }
        
        response = self.client.post(reverse('create_incident'), incident_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify incident was created
        self.assertTrue(Incident.objects.filter(title='New Test Incident').exists())

    def test_incident_edit(self):
        self.client.login(username='normal_user', password='testpass123')
        
        # Test editing own incident
        edit_data = {
            'title': 'Updated Test Incident',
            'description': 'Updated Description',
            'priority': 'Low',
            'state': 'In Progress',
            'affected_service': self.service.id,
            'incidentstart': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'assignee': self.normal_user.profile.id
        }
        
        response = self.client.post(
            reverse('incident_edit', kwargs={'incident_id': self.incident.id}),
            edit_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify changes
        updated_incident = Incident.objects.get(id=self.incident.id)
        self.assertEqual(updated_incident.title, 'Updated Test Incident')
        self.assertEqual(updated_incident.priority, 'Low')

    def test_incident_delete_permissions(self):
        # Test normal user deletion (should fail)
        self.client.login(username='normal_user', password='testpass123')
        response = self.client.post(reverse('incident_delete', kwargs={'incident_id': self.incident.id}))
        self.assertTrue(Incident.objects.filter(id=self.incident.id).exists())
        
        # Test staff user deletion (should succeed)
        self.client.login(username='staff_user', password='testpass123')
        response = self.client.post(reverse('incident_delete', kwargs={'incident_id': self.incident.id}))
        self.assertFalse(Incident.objects.filter(id=self.incident.id).exists())

    def test_incident_detail_view(self):
        self.client.login(username='normal_user', password='testpass123')
        
        response = self.client.get(reverse('incident_detail', kwargs={'incident_id': self.incident.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/incident_detail.html')
        self.assertEqual(response.context['incident'], self.incident)

class UserTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.django_group = Group.objects.create(name='User')
        self.user_group = UserGroup.objects.create(name='User Group')

    def test_user_creation(self):
        user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        response = self.client.post(reverse('user_create'), user_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after creation
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        
        # Verify user is in correct group
        user = User.objects.get(email='test@example.com')
        self.assertTrue(user.groups.filter(name='User').exists())

    def test_user_login(self):
        # Create a test user - UserProfile will be created automatically via signal
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.groups.add(self.django_group)
        user.profile.user_group = self.user_group
        user.profile.save()
        
        # Test login with username
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after login
        
        # Test login with email
        response = self.client.post(reverse('login'), {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

class ServiceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create superuser - UserProfile will be created automatically via signal
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

    def test_service_management(self):
        self.client.login(username='admin', password='adminpass123')
        
        # Test service creation
        service_data = {
            'name': 'New Service',
            'description': 'New Service Description',
            'status': 'Operational'
        }
        
        response = self.client.post(reverse('create_service'), service_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful creation
        self.assertTrue(Service.objects.filter(name='New Service').exists())
        
        # Get the created service
        service = Service.objects.get(name='New Service')
        
        # Test service update
        update_data = {
            'name': 'Updated Service',
            'description': 'Updated Description',
            'status': 'Degraded Performance'  
        }
        
        response = self.client.post(
            reverse('edit_service', kwargs={'service_id': service.id}),
            update_data
        )
        self.assertEqual(response.status_code, 302)  # Should redirect after successful update
        
        # Verify changes
        updated_service = Service.objects.get(id=service.id)
        self.assertEqual(updated_service.name, 'Updated Service')
        self.assertEqual(updated_service.status, 'Degraded Performance')
