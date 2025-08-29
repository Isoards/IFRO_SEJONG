import re
from django.core.management.base import BaseCommand
from traffic.models import Intersection
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Import intersections from a .sql file.'

    def add_arguments(self, parser):
        parser.add_argument('sql_file', type=str, help='The path to the .sql file to import.')

    def handle(self, *args, **options):
        sql_file_path = options['sql_file']
        
        if not os.path.exists(sql_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {sql_file_path}"))
            return

        self.stdout.write(f"Starting import from {sql_file_path}...")

        # 정규표현식으로 INSERT 구문 파싱
        insert_pattern = re.compile(
            r"INSERT INTO `traffic_intersection` \(`name`, `latitude`, `longitude`, `created_at`, `updated_at`\) VALUES "
            r"\('([^']*)', ([0-9.-]+), ([0-9.-]+), '([^']*)', '([^']*)'\);"
        )

        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading file: {e}"))
            return
            
        matches = insert_pattern.findall(content)
        
        if not matches:
            self.stderr.write(self.style.ERROR("No valid INSERT statements found."))
            return

        self.stdout.write(f"Found {len(matches)} records to import.")

        for match in matches:
            name, lat, lng, created_at, updated_at = match
            
            # update_or_create를 사용하여 데이터 중복 방지
            intersection, created = Intersection.objects.update_or_create(
                name=name,
                defaults={
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'created_at': created_at,
                    'updated_at': updated_at,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new intersection: {name}"))
            else:
                self.stdout.write(f"Updated existing intersection: {name}")

        self.stdout.write(self.style.SUCCESS('Successfully imported all intersections.')) 