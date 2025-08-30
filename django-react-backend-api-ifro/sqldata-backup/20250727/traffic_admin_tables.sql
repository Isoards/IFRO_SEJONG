-- Admin 관련 테이블 생성 스크립트

-- IntersectionStats 테이블 생성 (traffic 앱용)
CREATE TABLE IF NOT EXISTS `traffic_intersectionstats` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `intersection_id` bigint NOT NULL,
    `view_count` int unsigned NOT NULL DEFAULT '0',
    `favorite_count` int unsigned NOT NULL DEFAULT '0',
    `ai_report_count` int unsigned NOT NULL DEFAULT '0',
    `last_viewed` datetime(6) DEFAULT NULL,
    `last_ai_report` datetime(6) DEFAULT NULL,
    `created_at` datetime(6) NOT NULL,
    `updated_at` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `intersection_id` (`intersection_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- IntersectionViewLog 테이블 생성 (traffic 앱용)
CREATE TABLE IF NOT EXISTS `traffic_intersectionviewlog` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `intersection_id` bigint NOT NULL,
    `user_id` int DEFAULT NULL,
    `ip_address` char(39) NOT NULL,
    `user_agent` text,
    `viewed_at` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `traffic_intersectionviewlog_user_id_idx` (`user_id`),
    KEY `traffic_intersectionviewlog_intersection_id_idx` (`intersection_id`),
    KEY `traffic_intersectionviewlog_viewed_at_idx` (`viewed_at`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- IntersectionFavoriteLog 테이블 생성 (traffic 앱용)
CREATE TABLE IF NOT EXISTS `traffic_intersectionfavoritelog` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `intersection_id` bigint NOT NULL,
    `user_id` int NOT NULL,
    `is_favorite` tinyint(1) NOT NULL,
    `created_at` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `traffic_intersectionfavoritelog_user_id_idx` (`user_id`),
    KEY `traffic_intersectionfavoritelog_intersection_id_idx` (`intersection_id`),
    KEY `traffic_intersectionfavoritelog_created_at_idx` (`created_at`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
-- TrafficFlowAnalysisFavorite 테이블 생성 (교통 흐름 분석 즐겨찾기)
CREATE TABLE IF NOT EXISTS `traffic_trafficflowanalysisfavorite` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `start_intersection_id` bigint NOT NULL,
    `end_intersection_id` bigint NOT NULL,
    `total_favorites` int unsigned NOT NULL DEFAULT '0',
    `total_accesses` int unsigned NOT NULL DEFAULT '0',
    `unique_users` int unsigned NOT NULL DEFAULT '0',
    `last_accessed` datetime(6) DEFAULT NULL,
    `popularity_score` int unsigned NOT NULL DEFAULT '0',
    `created_at` datetime(6) NOT NULL,
    `updated_at` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `traffic_trafficflowanalysisfavorite_start_intersection_id_idx` (`start_intersection_id`),
    KEY `traffic_trafficflowanalysisfavorite_end_intersection_id_idx` (`end_intersection_id`),
    KEY `traffic_trafficflowanalysisfavorite_popularity_score_idx` (`popularity_score`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- TrafficFlowAnalysisStats 테이블 생성 (교통 흐름 분석 통계)
CREATE TABLE IF NOT EXISTS `traffic_trafficflowanalysisstats` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `start_intersection_id` bigint NOT NULL,
    `end_intersection_id` bigint NOT NULL,
    `total_favorites` int unsigned NOT NULL DEFAULT '0',
    `total_accesses` int unsigned NOT NULL DEFAULT '0',
    `created_at` datetime(6) NOT NULL,
    `updated_at` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `traffic_trafficflowanalysisstats_start_intersection_id_idx` (`start_intersection_id`),
    KEY `traffic_trafficflowanalysisstats_end_intersection_id_idx` (`end_intersection_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- 테스트 데이터 삽입

-- 교차로 조회 로그 테스트 데이터
INSERT INTO `traffic_intersectionviewlog` (`intersection_id`, `user_id`, `ip_address`, `user_agent`, `viewed_at`) VALUES
(127, 1, '127.0.0.1', 'Mozilla/5.0', '2025-08-30 02:00:00'),
(127, 1, '127.0.0.1', 'Mozilla/5.0', '2025-08-30 02:05:00'),
(127, 2, '192.168.1.1', 'Chrome/91.0', '2025-08-30 02:10:00'),
(2678, 1, '127.0.0.1', 'Mozilla/5.0', '2025-08-30 02:15:00'),
(2678, 3, '10.0.0.1', 'Safari/14.0', '2025-08-30 02:20:00'),
(493, 1, '127.0.0.1', 'Mozilla/5.0', '2025-08-30 02:25:00'),
(493, 2, '192.168.1.1', 'Chrome/91.0', '2025-08-30 02:30:00'),
(1199, 2, '192.168.1.1', 'Chrome/91.0', '2025-08-30 02:35:00'),
(1788, 3, '10.0.0.1', 'Safari/14.0', '2025-08-30 02:40:00'),
(3799, 1, '127.0.0.1', 'Mozilla/5.0', '2025-08-30 02:45:00');

-- 교차로 즐겨찾기 로그 테스트 데이터
INSERT INTO `traffic_intersectionfavoritelog` (`intersection_id`, `user_id`, `is_favorite`, `created_at`) VALUES
(127, 1, 1, '2025-08-30 02:00:00'),
(2678, 1, 1, '2025-08-30 02:05:00'),
(493, 2, 1, '2025-08-30 02:10:00'),
(1199, 2, 1, '2025-08-30 02:15:00'),
(1788, 3, 1, '2025-08-30 02:20:00');

-- 교통 흐름 분석 즐겨찾기 테스트 데이터 (TOP 5) - 주석처리
-- INSERT INTO `traffic_trafficflowanalysisfavorite` (`start_intersection_id`, `end_intersection_id`, `total_favorites`, `total_accesses`, `unique_users`, `last_accessed`, `popularity_score`, `created_at`, `updated_at`) VALUES
-- (3799, 493, 15, 120, 8, '2025-08-30 02:45:00', 95, '2025-08-30 01:00:00', '2025-08-30 02:45:00'),
-- (6506, 6028, 12, 98, 6, '2025-08-30 02:40:00', 88, '2025-08-30 01:05:00', '2025-08-30 02:40:00'),
-- (5517, 5019, 10, 85, 5, '2025-08-30 02:35:00', 82, '2025-08-30 01:10:00', '2025-08-30 02:35:00'),
-- (1788, 4177, 8, 72, 4, '2025-08-30 02:30:00', 75, '2025-08-30 01:15:00', '2025-08-30 02:30:00'),
-- (4589, 4100, 6, 58, 3, '2025-08-30 02:25:00', 68, '2025-08-30 01:20:00', '2025-08-30 02:25:00');

-- 교통 흐름 분석 통계 테스트 데이터
INSERT INTO `traffic_trafficflowanalysisstats` (`start_intersection_id`, `end_intersection_id`, `total_favorites`, `total_accesses`, `created_at`, `updated_at`) VALUES
(3799, 493, 15, 120, '2025-08-30 01:00:00', '2025-08-30 02:45:00'),
(6506, 6028, 12, 98, '2025-08-30 01:05:00', '2025-08-30 02:40:00'),
(5517, 5019, 10, 85, '2025-08-30 01:10:00', '2025-08-30 02:35:00'),
(1788, 4177, 8, 72, '2025-08-30 01:15:00', '2025-08-30 02:30:00'),
(4589, 4100, 6, 58, '2025-08-30 01:20:00', '2025-08-30 02:25:00');