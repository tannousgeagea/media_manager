# Generated by Django 4.2 on 2024-09-25 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0004_alter_media_media_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='media_type',
            field=models.CharField(choices=[('image', 'Image'), ('video', 'Video')], max_length=100),
        ),
    ]
