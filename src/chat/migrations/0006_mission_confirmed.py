# Generated by Django 5.1.1 on 2024-11-20 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_remove_mission_mission_time_mission_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mission',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
