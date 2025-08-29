import os
import json
from django.core.management.base import BaseCommand
from traffic.models import Intersection, TotalTrafficVolume
from django.utils.dateparse import parse_datetime

class Command(BaseCommand):
    help = "Import traffic intersections time-series data from JSON file."

    def handle(self, *args, **kwargs):
        # src/traffic/management/commands -> src/traffic/management -> src/traffic -> src -> 프로젝트 루트
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        PROJECT_ROOT = os.path.dirname(BASE_DIR)
        json_path = os.path.join(PROJECT_ROOT, 'database_data', 'traffic_intersections.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
        self.stdout.write(f"Loaded {len(data)} records from JSON.")

        # Intersection 캐싱
        intersection_cache = {}
        for item in data:
            key = (item['name'], item['latitude'], item['longitude'])
            if key not in intersection_cache:
                intersection, _ = Intersection.objects.get_or_create(
                    name=item['name'], latitude=item['latitude'], longitude=item['longitude']
                )
                intersection_cache[key] = intersection
        self.stdout.write(f"Cached {len(intersection_cache)} intersections.")

        # TotalTrafficVolume bulk insert
        TotalTrafficVolume.objects.all().delete()
        bulk = []
        for idx, item in enumerate(data, 1):
            key = (item['name'], item['latitude'], item['longitude'])
            intersection = intersection_cache[key]
            bulk.append(TotalTrafficVolume(
                intersection=intersection,
                datetime=parse_datetime(item['datetime']),
                total_volume=item['total_volume'],
                average_speed=item['average_speed'],
            ))
            if idx % 10000 == 0:
                self.stdout.write(f"Prepared {idx} records...")

        # 실제 DB에 한 번에 저장 (batch_size는 2000)
        TotalTrafficVolume.objects.bulk_create(bulk, batch_size=2000)
        self.stdout.write(self.style.SUCCESS("Import completed!")) 