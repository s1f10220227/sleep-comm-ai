# Generated by Django 5.1.2 on 2024-12-04 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='age',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='gender',
            field=models.CharField(choices=[('male', '男性'), ('female', '女性'), ('unspecified', '未回答')], default='unspecified', max_length=12),
        ),
    ]
