-- MySQL dump 10.13  Distrib 8.0.42, for Linux (aarch64)
--
-- Host: localhost    Database: traffic
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `traffic_policyproposal`
--

DROP TABLE IF EXISTS `traffic_policyproposal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_policyproposal` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `priority` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'medium',
  `status` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `location` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `admin_response` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `admin_response_date` datetime(6) DEFAULT NULL,
  `votes_count` int NOT NULL DEFAULT '0',
  `views_count` int NOT NULL DEFAULT '0',
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `admin_response_by_id` bigint DEFAULT NULL,
  `intersection_id` bigint DEFAULT NULL,
  `submitted_by_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `admin_response_by_id` (`admin_response_by_id`),
  KEY `intersection_id` (`intersection_id`),
  KEY `submitted_by_id` (`submitted_by_id`),
  CONSTRAINT `traffic_policyproposal_ibfk_1` FOREIGN KEY (`admin_response_by_id`) REFERENCES `user_auth_user` (`id`),
  CONSTRAINT `traffic_policyproposal_ibfk_2` FOREIGN KEY (`intersection_id`) REFERENCES `traffic_intersection` (`id`),
  CONSTRAINT `traffic_policyproposal_ibfk_3` FOREIGN KEY (`submitted_by_id`) REFERENCES `user_auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traffic_proposalattachment`
--

DROP TABLE IF EXISTS `traffic_proposalattachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_proposalattachment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_size` int unsigned NOT NULL,
  `uploaded_at` datetime(6) NOT NULL,
  `proposal_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `proposal_id` (`proposal_id`),
  CONSTRAINT `traffic_proposalattachment_ibfk_1` FOREIGN KEY (`proposal_id`) REFERENCES `traffic_policyproposal` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traffic_proposaltag`
--

DROP TABLE IF EXISTS `traffic_proposaltag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_proposaltag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traffic_proposaltag_proposals`
--

DROP TABLE IF EXISTS `traffic_proposaltag_proposals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_proposaltag_proposals` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `proposaltag_id` bigint NOT NULL,
  `policyproposal_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `proposaltag_id` (`proposaltag_id`,`policyproposal_id`),
  KEY `policyproposal_id` (`policyproposal_id`),
  CONSTRAINT `traffic_proposaltag_proposals_ibfk_1` FOREIGN KEY (`proposaltag_id`) REFERENCES `traffic_proposaltag` (`id`),
  CONSTRAINT `traffic_proposaltag_proposals_ibfk_2` FOREIGN KEY (`policyproposal_id`) REFERENCES `traffic_policyproposal` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traffic_proposalviewlog`
--

DROP TABLE IF EXISTS `traffic_proposalviewlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_proposalviewlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ip_address` char(39) COLLATE utf8mb4_unicode_ci NOT NULL,
  `viewed_at` datetime(6) NOT NULL,
  `proposal_id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `proposal_id` (`proposal_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `traffic_proposalviewlog_ibfk_1` FOREIGN KEY (`proposal_id`) REFERENCES `traffic_policyproposal` (`id`),
  CONSTRAINT `traffic_proposalviewlog_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user_auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `traffic_proposalvote`
--

DROP TABLE IF EXISTS `traffic_proposalvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_proposalvote` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `vote_type` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `proposal_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `proposal_id` (`proposal_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `traffic_proposalvote_ibfk_1` FOREIGN KEY (`proposal_id`) REFERENCES `traffic_policyproposal` (`id`),
  CONSTRAINT `traffic_proposalvote_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user_auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'traffic'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-30  4:07:46
