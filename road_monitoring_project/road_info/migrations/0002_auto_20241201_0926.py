# Generated by Django 3.2.23 on 2024-12-01 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('road_info', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roadinfo',
            name='image_path',
        ),
        migrations.AddField(
            model_name='roadinfo',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='road_images/'),
        ),
    ]
