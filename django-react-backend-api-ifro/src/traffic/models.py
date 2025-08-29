from django.db import models
from django.utils import timezone

# Create your models here.

class Intersection(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class TrafficVolume(models.Model):
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='traffic_volumes')
    datetime = models.DateTimeField()
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    volume = models.IntegerField()
    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime} - {self.direction}"

    class Meta:
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['direction']),
        ]

# 프론트엔드에서 시간별 교차로 데이터(total_volume, average_speed, datetime 등)를 사용할 때 이 모델을 활용합니다.
class TotalTrafficVolume(models.Model):
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    total_volume = models.IntegerField()
    average_speed = models.FloatField()

    class Meta:
        db_table = 'total_traffic_volume'
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime}: {self.total_volume}대, {self.average_speed}km/h"

class TrafficInterpretation(models.Model):
    CONGESTION_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='interpretations')
    datetime = models.DateTimeField()
    interpretation_text = models.TextField()
    congestion_level = models.CharField(max_length=20, choices=CONGESTION_LEVEL_CHOICES)
    peak_direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['intersection', 'datetime']
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['congestion_level']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime} - {self.congestion_level}"

class Incident(models.Model):
    incident_id = models.AutoField(primary_key=True)
    incident_type = models.CharField(max_length=100, verbose_name="Incident Type", default="")
    intersection_name = models.CharField(max_length=200, verbose_name="Intersection Name", default="")
    district = models.CharField(max_length=100, verbose_name="District", default="")
    managed_by = models.CharField(max_length=100, verbose_name="Managed By", default="")
    assigned_to = models.CharField(max_length=100, verbose_name="Assigned To", default="")
    registered_at = models.DateTimeField(verbose_name="Registered At", auto_now_add=True)
    status = models.CharField(max_length=50, verbose_name="Status", default="OPEN")
    user = models.CharField(max_length=100, verbose_name="User", default="")
    equipment_locked = models.CharField(max_length=1, choices=[('S', 'Yes'), ('N', 'No')], verbose_name="Equipment Locked", default='N')
    last_status_update = models.DateTimeField(auto_now=True, verbose_name="Last Status Update")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    sii_id = models.IntegerField(null=True, blank=True, verbose_name="SII ID")
    intersection = models.ForeignKey("Intersection", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Linked Intersection")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    type = models.CharField(max_length=100, verbose_name="Type", default="")

    def __str__(self):
        return f"{self.incident_id} - {self.intersection_name} - {self.status}"

    class Meta:
        ordering = ['-registered_at']
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        indexes = [
            models.Index(fields=['incident_type']),
            models.Index(fields=['status']),
            models.Index(fields=['registered_at']),
            models.Index(fields=['district']),
            models.Index(fields=['intersection']),
        ]

# --- Secure Models ---

class S_TrafficVolume(models.Model):
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='s_traffic_volumes')
    datetime = models.DateTimeField()
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    volume = models.IntegerField()
    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"S_{self.intersection.name} - {self.datetime} - {self.direction}"

    class Meta:
        db_table = 'S_traffic_volume'
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['direction']),
        ]

class S_TotalTrafficVolume(models.Model):
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='s_total_traffic_volumes')
    datetime = models.DateTimeField()
    total_volume = models.IntegerField()
    average_speed = models.FloatField()

    class Meta:
        db_table = 'S_total_traffic_volume'
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
        ]

    def __str__(self):
        return f"S_{self.intersection.name} - {self.datetime}: {self.total_volume}대, {self.average_speed}km/h"

class S_TrafficInterpretation(models.Model):
    CONGESTION_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='s_interpretations')
    datetime = models.DateTimeField()
    interpretation_text = models.TextField()
    congestion_level = models.CharField(max_length=20, choices=CONGESTION_LEVEL_CHOICES)
    peak_direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'S_traffic_interpretation'
        unique_together = ['intersection', 'datetime']
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['congestion_level']),
        ]

    def __str__(self):
        return f"S_{self.intersection.name} - {self.datetime} - {self.congestion_level}"

class S_Incident(models.Model):
    incident_id = models.AutoField(primary_key=True)
    incident_type = models.CharField(max_length=100, verbose_name="Incident Type", default="")
    intersection_name = models.CharField(max_length=200, verbose_name="Intersection Name", default="")
    district = models.CharField(max_length=100, verbose_name="District", default="")
    managed_by = models.CharField(max_length=100, verbose_name="Managed By", default="")
    assigned_to = models.CharField(max_length=100, verbose_name="Assigned To", default="")
    registered_at = models.DateTimeField(verbose_name="Registered At", auto_now_add=True)
    status = models.CharField(max_length=50, verbose_name="Status", default="OPEN")
    user = models.CharField(max_length=100, verbose_name="User", default="")
    equipment_locked = models.CharField(max_length=1, choices=[('S', 'Yes'), ('N', 'No')], verbose_name="Equipment Locked", default='N')
    last_status_update = models.DateTimeField(auto_now=True, verbose_name="Last Status Update")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    sii_id = models.IntegerField(null=True, blank=True, verbose_name="SII ID")
    intersection = models.ForeignKey("Intersection", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Linked Intersection", related_name='s_incidents')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    type = models.CharField(max_length=100, verbose_name="Type", default="")

    def __str__(self):
        return f"S_{self.incident_id} - {self.intersection_name} - {self.status}"

    class Meta:
        db_table = 'S_incident'
        ordering = ['-registered_at']
        verbose_name = "Secure Incident"
        verbose_name_plural = "Secure Incidents"
        indexes = [
            models.Index(fields=['incident_type']),
            models.Index(fields=['status']),
            models.Index(fields=['registered_at']),
            models.Index(fields=['district']),
            models.Index(fields=['intersection']),
        ]
