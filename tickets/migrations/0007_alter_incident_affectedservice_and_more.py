# Generated by Django 5.1.2 on 2024-12-19 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_alter_incident_affectedservice_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incident',
            name='affectedservice',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='incidentcreated',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='incidentstart',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='priority',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='state',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='incident',
            name='title',
            field=models.TextField(),
        ),
    ]