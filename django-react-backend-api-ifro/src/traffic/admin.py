from django.contrib import admin
from .models import Intersection, TrafficVolume, TotalTrafficVolume

@admin.register(Intersection)
class IntersectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')

@admin.register(TrafficVolume)
class TrafficVolumeAdmin(admin.ModelAdmin):
    list_display = ('intersection', 'datetime', 'direction', 'volume', 'is_simulated', 'created_at')
    list_filter = ('intersection', 'direction', 'is_simulated', 'datetime')
    search_fields = ('intersection__name',)
    date_hierarchy = 'datetime'
    ordering = ('-datetime',)

admin.site.register(TotalTrafficVolume)
