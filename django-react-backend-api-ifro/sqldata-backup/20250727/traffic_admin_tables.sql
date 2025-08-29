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