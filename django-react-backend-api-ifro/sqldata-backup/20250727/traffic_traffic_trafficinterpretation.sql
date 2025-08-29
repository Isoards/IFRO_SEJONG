-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: traffic
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `traffic_trafficinterpretation`
--

DROP TABLE IF EXISTS `traffic_trafficinterpretation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `traffic_trafficinterpretation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `intersection_id` bigint NOT NULL,
  `datetime` datetime(6) NOT NULL,
  `interpretation_text` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `congestion_level` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `peak_direction` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `traffic_trafficinterpretation_intersection_datetime_unique` (`intersection_id`,`datetime`),
  KEY `traffic_trafficinterpretation_intersection_datetime_idx` (`intersection_id`,`datetime`),
  KEY `traffic_trafficinterpretation_congestion_level_idx` (`congestion_level`),
  CONSTRAINT `traffic_trafficinterpretation_intersection_id_fkey` FOREIGN KEY (`intersection_id`) REFERENCES `traffic_intersection` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `traffic_trafficinterpretation`
--

LOCK TABLES `traffic_trafficinterpretation` WRITE;
/*!40000 ALTER TABLE `traffic_trafficinterpretation` DISABLE KEYS */;
/*!40000 ALTER TABLE `traffic_trafficinterpretation` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-27  3:34:20
