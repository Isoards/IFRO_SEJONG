#!/usr/bin/env python
import os
import sys
import django

# Django 설정
sys.path.append('/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from django.db import connection

def create_tables():
    with connection.cursor() as cursor:
        # 교통 흐름 분석 즐겨찾기 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `traffic_trafficflowanalysisfavorite` (
                `id` bigint NOT NULL AUTO_INCREMENT,
                `favorite_name` varchar(200) NOT NULL,
                `created_at` datetime(6) NOT NULL,
                `last_accessed` datetime(6) DEFAULT NULL,
                `access_count` int unsigned NOT NULL DEFAULT '0',
                `user_id` bigint NOT NULL,
                `start_intersection_id` bigint NOT NULL,
                `end_intersection_id` bigint NOT NULL,
                PRIMARY KEY (`id`),
                UNIQUE KEY `flow_fav_user_start_end_uniq` (`user_id`,`start_intersection_id`,`end_intersection_id`),
                KEY `flow_fav_user_created_idx` (`user_id`,`created_at`),
                KEY `flow_fav_start_end_idx` (`start_intersection_id`,`end_intersection_id`),
                KEY `flow_fav_access_idx` (`access_count`),
                KEY `flow_fav_last_access_idx` (`last_accessed`),
                KEY `flow_fav_start_fk` (`start_intersection_id`),
                KEY `flow_fav_end_fk` (`end_intersection_id`),
                CONSTRAINT `flow_fav_user_fk` FOREIGN KEY (`user_id`) REFERENCES `user_auth_user` (`id`),
                CONSTRAINT `flow_fav_start_fk` FOREIGN KEY (`start_intersection_id`) REFERENCES `traffic_intersection` (`id`),
                CONSTRAINT `flow_fav_end_fk` FOREIGN KEY (`end_intersection_id`) REFERENCES `traffic_intersection` (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        # 교통 흐름 분석 통계 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `traffic_trafficflowanalysisstats` (
                `id` bigint NOT NULL AUTO_INCREMENT,
                `total_favorites` int unsigned NOT NULL DEFAULT '0',
                `total_accesses` int unsigned NOT NULL DEFAULT '0',
                `unique_users` int unsigned NOT NULL DEFAULT '0',
                `last_accessed` datetime(6) DEFAULT NULL,
                `created_at` datetime(6) NOT NULL,
                `updated_at` datetime(6) NOT NULL,
                `start_intersection_id` bigint NOT NULL,
                `end_intersection_id` bigint NOT NULL,
                PRIMARY KEY (`id`),
                UNIQUE KEY `flow_stats_start_end_uniq` (`start_intersection_id`,`end_intersection_id`),
                KEY `flow_stats_total_fav_idx` (`total_favorites`),
                KEY `flow_stats_total_acc_idx` (`total_accesses`),
                KEY `flow_stats_unique_users_idx` (`unique_users`),
                KEY `flow_stats_last_access_idx` (`last_accessed`),
                KEY `flow_stats_start_fk` (`start_intersection_id`),
                KEY `flow_stats_end_fk` (`end_intersection_id`),
                CONSTRAINT `flow_stats_start_fk` FOREIGN KEY (`start_intersection_id`) REFERENCES `traffic_intersection` (`id`),
                CONSTRAINT `flow_stats_end_fk` FOREIGN KEY (`end_intersection_id`) REFERENCES `traffic_intersection` (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        
        print("테이블이 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    create_tables()