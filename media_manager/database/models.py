import hashlib
from django.db import models


def get_media_path(instance, filename):
    return f"{instance.event.event_name}/{instance.event.event_id}/{instance.media_type}_{instance.media_id}_{filename}"

# Create your models here.
class PlantInfo(models.Model):
    plant_id = models.CharField(max_length=255, unique=True)
    plant_name = models.CharField(max_length=255)
    plant_location = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'plant_info'
        verbose_name_plural = 'Plant Information'
        unique_together = ('plant_name', 'plant_location')

    def __str__(self):
        return f"{self.plant_name} in {self.plant_location}"
    
class EdgeBoxInfo(models.Model):
    plant = models.ForeignKey(PlantInfo, on_delete=models.CASCADE)
    edge_box_id = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info =  models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'edge_box_info'
        verbose_name_plural = 'EdgeBox Information'
        unique_together = ('plant', "edge_box_id")
    
    def __str__(self):
        return f'{self.edge_box_id}'

    
class Event(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    edge_box = models.ForeignKey(EdgeBoxInfo, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=255, unique=True)
    event_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_description = models.TextField()
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='pending')
    status_description = models.TextField(null=True, blank=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'event'
        verbose_name_plural = 'Events'
        unique_together = ('edge_box', "event_id")
    
    def __str__(self):
        return f"{self.event_name}"

class Media(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video')
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_index=True)
    source_id = models.CharField(max_length=255)
    media_id = models.CharField(max_length=255, unique=True, db_index=True)
    media_name = models.CharField(max_length=255)
    media_type = models.CharField(max_length=100, choices=MEDIA_TYPE_CHOICES)
    media_file = models.FileField(upload_to=get_media_path, max_length=255)
    file_size = models.BigIntegerField(null=True, blank=True)  # Store size in bytes
    duration = models.DurationField(null=True, blank=True)  # Duration for videos
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'media'
        verbose_name_plural = 'Media'
        unique_together = ('event', "media_id")
        
    def __str__(self):
        return f"{self.event}, {self.media_name}, {self.media_type}"