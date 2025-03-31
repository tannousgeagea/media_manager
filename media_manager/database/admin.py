from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import PlantInfo, EdgeBoxInfo, Event, Media

admin.site.site_header = "Media Manager"
admin.site.site_title = "media Manager"
admin.site.index_title = "Welcome to Media Manager DB"

# Customizing the PlantInfo admin interface
@admin.register(PlantInfo)
class PlantInfoAdmin(ModelAdmin):
    list_display = ('plant_name', 'plant_location', 'domain', 'created_at')  # Display these fields in the admin list view
    search_fields = ('plant_name', 'plant_location', 'domain')  # Enable search by these fields
    list_filter = ('domain', 'created_at')  # Add filter options on the sidebar
    ordering = ('-created_at',)  # Default ordering by the newest created items
    readonly_fields = ('created_at',)  # Make created_at read-only

# Customizing the EdgeBoxInfo admin interface
@admin.register(EdgeBoxInfo)
class EdgeBoxInfoAdmin(ModelAdmin):
    list_display = ('plant', 'edge_box_id', 'location', 'created_at')  # Fields to show in the list view
    search_fields = ('edge_box_id', 'edge_box_location')  # Enable search by these fields
    list_filter = ('plant', 'created_at')  # Add filter options for plant and created_at
    ordering = ('-created_at',)  # Order by created_at, descending

# Customizing the Event admin interface
@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ('event_name', 'edge_box', 'event_type', 'status', 'timestamp', 'created_at')  # Show important fields in the list view
    search_fields = ('event_name', 'event_id', 'event_type')  # Enable search by event fields
    list_filter = ('status', 'event_type', 'timestamp', 'created_at')  # Add filters for status, type, timestamp, and creation date
    ordering = ('-timestamp',)  # Default ordering by timestamp (latest first)
    readonly_fields = ('created_at',)  # Make created_at read-only
    fieldsets = (
        ('Event Information', {
            'fields': ('event_name', 'event_id', 'edge_box', 'event_type', 'timestamp', 'event_description', 'meta_info')
        }),
        ('Status', {
            'fields': ('status', 'status_description')
        }),
        ('Additional Information', {
            'fields': ('created_at',)
        })
    )  # Organize fields in collapsible sections

# Customizing the Media admin interface
@admin.register(Media)
class MediaAdmin(ModelAdmin):
    list_display = ('media_name', 'media_type', 'event', 'media_file', 'source_id', 'show_media_size', 'duration', 'created_at')  # List these fields in the media list view
    search_fields = ('media_name', 'media_id', 'event__event_name')  # Enable search by media name, ID, and event name
    list_filter = ('media_type', 'created_at', 'event__edge_box__plant')  # Add filter options for media type, date, and plant
    ordering = ('-created_at',)  # Order by the most recent creation date
    readonly_fields = ('created_at',)  # Make created_at read-only
    fieldsets = (
        ('Media Information', {
            'fields': ('media_name', 'media_id', 'media_type', 'event', 'media_file')
        }),
        ('File Details', {
            'fields': ('file_size', 'duration', 'meta_info')
        }),
        ('Additional Information', {
            'fields': ('created_at',)
        })
    )  # Organize fields into collapsible sections


    def show_media_size(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f}" if obj.file_size else obj.file_size
    show_media_size.short_description = "Size (MB)"