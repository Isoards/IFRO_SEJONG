from django.core.management.base import BaseCommand
from traffic.models import Intersection, Incident
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generate 50 fake Incident data based on existing intersections.'

    def handle(self, *args, **kwargs):
        incident_types = [
            "PROBLEM - INTERSECTION",
            "WORKS - OPERATOR",
            "WORKS - PROGRAMMER",
            "PROBLEM - PERIPHERALS"
        ]
        types = [
            "POWER OUTAGE",
            "MONITORING",
            "SCHEDULED OUTAGE",
            "BULB FAILURE",
            "SYNC - FIELD",
            "STRUCTURE DAMAGED",
            "CAMERA - NO SIGNAL",
            "GPS TRACKING",
            "INTERMITTENT SIGNAL"
        ]
        districts = [
            "LIMA", "RIMAC", "CHORRILLOS", "ATE", "SURCO", "VICTORIA", "PUEBLO LIBRE", "SAN MIGUEL"
        ]
        managed_by = ["GMU - CENTRALIZED", "GMU - NON CENTRALIZED"]
        assigned_to = ["OPERATOR CCGT", "PROGRAMMER CCGT", "DIESM - CENTRALIZED"]
        status_choices = ["ASSIGNED", "RESOLVED", "OPEN"]
        users = ["testuser", "mmamani", "mcarrasco"]

        intersections = list(Intersection.objects.all())
        if not intersections:
            self.stdout.write(self.style.ERROR('No intersections found in the database.'))
            return

        # 기존 Incident 데이터 삭제 (테스트 목적)
        Incident.objects.all().delete()

        incidents = []
        for i in range(50):
            intersection = random.choice(intersections)
            incidents.append(Incident(
                incident_type=random.choice(incident_types),
                type=random.choice(types),
                intersection_name=intersection.name,  # 실제 DB에 있는 이름
                district=random.choice(districts),
                managed_by=random.choice(managed_by),
                assigned_to=random.choice(assigned_to),
                status=random.choice(status_choices),
                user=random.choice(users),
                equipment_locked=random.choice(["S", "N"]),
                intersection=intersection,  # 실제 객체 연결
                registered_at=timezone.now(),
                last_status_update=timezone.now(),
            ))

        Incident.objects.bulk_create(incidents)
        self.stdout.write(self.style.SUCCESS('실제 intersection 기반 Incident 50개 생성 완료!')) 