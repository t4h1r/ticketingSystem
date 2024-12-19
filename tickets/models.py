from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserGroup(models.Model):
    name = models.CharField(max_length=100, default='Default Group')
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'usergroups'

class UserProfile(models.Model):
    user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE, related_name='profile')
    department = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        db_table = 'users'

class Service(models.Model):
    STATUS_CHOICES = [
        ('Operational', 'Operational'),
        ('Degraded Performance', 'Degraded Performance'),
        ('Partial Outage', 'Partial Outage'),
        ('Major Outage', 'Major Outage'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Operational')
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'services'
        ordering = ['name']

class Incident(models.Model):
    title = models.TextField(null=False, blank=False)
    assignee = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    assignedgroup = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    reportedby = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_incidents')
    affected_service = models.ForeignKey(
        Service, 
        on_delete=models.PROTECT, 
        null=True,  # Temporarily allow null for migration
        blank=True
    )
    incidentcreated = models.DateTimeField(null=False, blank=False)
    incidentstart = models.DateTimeField(null=False, blank=False)
    priority = models.TextField(null=False, blank=False)
    state = models.TextField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    resolution = models.TextField(null=True, blank=True)
    incidentclosedtime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        db_table = 'incidents'

@receiver(post_save, sender=DjangoUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=DjangoUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()