# Generated by Django 5.1.2 on 2024-12-19 13:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0007_alter_incident_affectedservice_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('Running', 'Running'), ('Disruption', 'Disruption')], default='Running', max_length=20)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tickets.userprofile')),
            ],
            options={
                'db_table': 'services',
                'ordering': ['name'],
            },
        ),
    ]
