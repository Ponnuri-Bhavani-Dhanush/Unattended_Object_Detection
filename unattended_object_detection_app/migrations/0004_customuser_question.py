# Generated by Django 4.1 on 2023-03-20 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unattended_object_detection_app', '0003_alter_customuser_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='question',
            field=models.CharField(default='Groot', max_length=40),
        ),
    ]