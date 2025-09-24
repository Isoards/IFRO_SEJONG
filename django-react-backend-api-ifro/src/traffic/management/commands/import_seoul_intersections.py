import os
import json
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from datetime import datetime

class Command(BaseCommand):
    help = "Import Seoul intersection data from JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default='/home/aprang2261/IFRO_SEJONG/seoul-intersection-data/서울시 교차로 관련 정보.json',
            help='Path to Seoul intersection JSON file'
        )

    def epsg5186_to_latlon(self, x, y):
        """
        EPSG:5186 (Korea 2000 / Korea Central Belt 2010) 좌표를 WGS84 위도/경도로 변환
        """
        try:
            from pyproj import Transformer
            
            # EPSG:5186에서 WGS84 (EPSG:4326)로 변환
            transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(x, y)
            
            return lat, lon
            
        except ImportError:
            # pyproj가 없는 경우 근사치 변환 사용
            import math
            
            # EPSG:5186은 한국 중부원점 좌표계
            # 근사치 변환 (정확하지 않으므로 pyproj 사용 권장)
            lat = 37.5 + (y - 200000) / 111000.0
            lon = 127.0 + (x - 500000) / (111000.0 * math.cos(math.radians(37.5)))
            
            return lat, lon

    def clear_existing_data(self):
        """기존 교차로 데이터 삭제"""
        self.stdout.write("기존 교차로 데이터를 삭제하는 중...")
        
        with connection.cursor() as cursor:
            # 외래키 제약조건을 일시적으로 비활성화
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 관련 테이블들 삭제
            tables_to_clear = [
                'traffic_trafficflowanalysisfavorite',
                'traffic_trafficflowanalysisstats', 
                'traffic_trafficinterpretation',
                'traffic_trafficvolume',
                'total_traffic_volume',
                'traffic_incident',
                'S_traffic_volume',
                'S_total_traffic_volume', 
                'S_traffic_interpretation',
                'S_incident',
                'traffic_intersectionstats',
                'traffic_intersectionviewlog',
                'traffic_intersectionfavoritelog',
                'traffic_policyproposal',
                'traffic_proposalattachment',
                'traffic_proposalvote',
                'traffic_proposalviewlog',
                'traffic_proposaltag',
                'traffic_intersection'
            ]
            
            for table in tables_to_clear:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    self.stdout.write(f"✓ {table} 데이터 삭제 완료")
                except Exception as e:
                    self.stdout.write(f"⚠ {table} 삭제 중 오류 (테이블이 존재하지 않을 수 있음): {e}")
            
            # 외래키 제약조건 재활성화
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        self.stdout.write("기존 데이터 삭제 완료!")

    def import_seoul_intersections(self, json_file_path):
        """서울 교차로 데이터를 MySQL에 삽입"""
        self.stdout.write("서울 교차로 데이터를 가져오는 중...")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        intersections_data = data.get('DATA', [])
        self.stdout.write(f"총 {len(intersections_data)}개의 교차로 데이터를 발견했습니다.")
        
        # 교차로 데이터 변환 및 삽입
        intersections_to_insert = []
        processed_count = 0
        
        for item in intersections_data:
            try:
                # 교차로명칭
                name = item.get('intr_nm', '').strip()
                if not name:
                    continue
                    
                # X, Y 좌표 (EPSG:5186)
                x_coord = item.get('xcrd')
                y_coord = item.get('ycrd')
                
                if not x_coord or not y_coord:
                    continue
                    
                # EPSG:5186을 위도/경도로 변환
                try:
                    latitude, longitude = self.epsg5186_to_latlon(float(x_coord), float(y_coord))
                except (ValueError, TypeError):
                    continue
                
                # 교차로 데이터 추가
                intersections_to_insert.append({
                    'name': name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
                
                processed_count += 1
                
                if processed_count % 1000 == 0:
                    self.stdout.write(f"처리 중... {processed_count}개 완료")
                    
            except Exception as e:
                self.stdout.write(f"데이터 처리 중 오류: {e}")
                continue
        
        self.stdout.write(f"변환 완료: {len(intersections_to_insert)}개의 교차로 데이터")
        
        # MySQL에 일괄 삽입
        if intersections_to_insert:
            self.stdout.write("MySQL 데이터베이스에 삽입하는 중...")
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 교차로 데이터 일괄 삽입
                    insert_query = """
                    INSERT INTO traffic_intersection (name, latitude, longitude, created_at, updated_at)
                    VALUES (%(name)s, %(latitude)s, %(longitude)s, %(created_at)s, %(updated_at)s)
                    """
                    
                    cursor.executemany(insert_query, intersections_to_insert)
                    
            self.stdout.write(f"✓ {len(intersections_to_insert)}개의 교차로가 성공적으로 삽입되었습니다!")
        
        return len(intersections_to_insert)

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        
        self.stdout.write("=== 서울 교차로 데이터 임포트 시작 ===")
        
        try:
            # 1. 기존 데이터 삭제
            self.clear_existing_data()
            
            # 2. 서울 교차로 데이터 임포트
            inserted_count = self.import_seoul_intersections(json_file_path)
            
            self.stdout.write(f"\n=== 임포트 완료 ===")
            self.stdout.write(f"총 {inserted_count}개의 서울 교차로가 데이터베이스에 추가되었습니다.")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"오류 발생: {e}"))
            return
