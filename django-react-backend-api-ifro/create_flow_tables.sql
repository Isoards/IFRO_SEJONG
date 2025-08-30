-- 교통 흐름 분석 즐겨찾기 테이블 생성
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
    UNIQUE KEY `traffic_trafficflowanalys_user_id_start_intersecti_8a8a8a8a_uniq` (`user_id`,`start_intersection_id`,`end_intersection_id`),
    KEY `traffic_tra_user_id_e8e8e8_idx` (`user_id`,`created_at`),
    KEY `traffic_tra_start_i_f8f8f8_idx` (`start_intersection_id`,`end_intersection_id`),
    KEY `traffic_tra_access__a8a8a8_idx` (`access_count`),
    KEY `traffic_tra_last_ac_b8b8b8_idx` (`last_accessed`),
    KEY `traffic_trafficflowanalysisfavorite_start_intersection_id_8b8b8b8b_fk` (`start_intersection_id`),
    KEY `traffic_trafficflowanalysisfavorite_end_intersection_id_9c9c9c9c_fk` (`end_intersection_id`),
    CONSTRAINT `traffic_trafficflowanalysisfavorite_user_id_1a1a1a1a_fk` FOREIGN KEY (`user_id`) REFERENCES `user_auth_user` (`id`),
    CONSTRAINT `traffic_trafficflowanalysisfavorite_start_intersection_id_8b8b8b8b_fk` FOREIGN KEY (`start_intersection_id`) REFERENCES `traffic_intersection` (`id`),
    CONSTRAINT `traffic_trafficflowanalysisfavorite_end_intersection_id_9c9c9c9c_fk` FOREIGN KEY (`end_intersection_id`) REFERENCES `traffic_intersection` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 교통 흐름 분석 통계 테이블 생성
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
    UNIQUE KEY `traffic_trafficflowanalys_start_intersection_id_en_2b2b2b2b_uniq` (`start_intersection_id`,`end_intersection_id`),
    KEY `traffic_tra_total_f_c8c8c8_idx` (`total_favorites`),
    KEY `traffic_tra_total_a_d8d8d8_idx` (`total_accesses`),
    KEY `traffic_tra_unique__e8e8e8_idx` (`unique_users`),
    KEY `traffic_tra_last_ac_f8f8f8_idx` (`last_accessed`),
    KEY `traffic_trafficflowanalysisstats_end_intersection_id_3c3c3c3c_fk` (`end_intersection_id`),
    CONSTRAINT `traffic_trafficflowanalysisstats_start_intersection_id_4d4d4d4d_fk` FOREIGN KEY (`start_intersection_id`) REFERENCES `traffic_intersection` (`id`),
    CONSTRAINT `traffic_trafficflowanalysisstats_end_intersection_id_3c3c3c3c_fk` FOREIGN KEY (`end_intersection_id`) REFERENCES `traffic_intersection` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;