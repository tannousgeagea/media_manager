# Generated by Django 4.2 on 2024-09-25 11:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0006_alter_media_media_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='source_id',
            field=models.CharField(default=django.utils.timezone.now, max_length=255),
            preserve_default=False,
        ),
    ]
