# Generated by Django 5.1.2 on 2024-12-19 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0009_remove_incident_affectedservice_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='incident',
            name='affected_service',
        ),
        migrations.AddField(
            model_name='incident',
            name='affectedservice',
            field=models.TextField(default='Unknown Service'),
        ),
    ]
