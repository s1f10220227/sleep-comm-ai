# Generated by Django 5.1.1 on 2024-11-20 06:58

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_mission'),
        ('groups', '0003_alter_groupmember_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mission',
            name='mission_time',
        ),
        migrations.AddField(
            model_name='mission',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mission',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='groups.group'),
        ),
    ]
