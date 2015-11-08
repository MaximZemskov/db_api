-- MySQL dump 10.13  Distrib 5.6.24, for linux-glibc2.5 (x86_64)
--
-- Host: localhost    Database: db
-- ------------------------------------------------------
-- Server version	5.5.41-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `followers`
--

DROP TABLE IF EXISTS `followers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `followers` (
  `who_user` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  `whom_user` varchar(64) CHARACTER SET utf8 DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `followers`
--

LOCK TABLES `followers` WRITE;
/*!40000 ALTER TABLE `followers` DISABLE KEYS */;
/*!40000 ALTER TABLE `followers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forums`
--

DROP TABLE IF EXISTS `forums`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `forums` (
  `name` varchar(64) DEFAULT NULL,
  `short_name` varchar(64) DEFAULT NULL,
  `user` varchar(64) DEFAULT NULL,
  `forum_id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`forum_id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  UNIQUE KEY `short_name_UNIQUE` (`short_name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forums`
--

LOCK TABLES `forums` WRITE;
/*!40000 ALTER TABLE `forums` DISABLE KEYS */;
INSERT INTO `forums` VALUES ('Forum With Sufficiently Large Name','forumwithsufficientlylargename','example2@mail.ru',1),('Forum I','forum1','richard.nixon@example.com',2),('Forum II','forum2','richard.nixon@example.com',3),('Форум Три','forum3','richard.nixon@example.com',4);
/*!40000 ALTER TABLE `forums` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `posts` (
  `post_id` int(11) NOT NULL AUTO_INCREMENT,
  `parent` int(11) DEFAULT NULL,
  `isApproved` tinyint(1) DEFAULT NULL,
  `isEdited` tinyint(1) DEFAULT NULL,
  `isSpam` tinyint(1) DEFAULT NULL,
  `isDeleted` tinyint(1) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `message` text CHARACTER SET utf8,
  `user` varchar(45) CHARACTER SET utf8 DEFAULT NULL,
  `forum` varchar(45) CHARACTER SET utf8 DEFAULT NULL,
  `dislikes` int(11) DEFAULT '0',
  `likes` int(11) DEFAULT '0',
  `thread` int(11) DEFAULT NULL,
  `isHighlited` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`post_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `posts`
--

LOCK TABLES `posts` WRITE;
/*!40000 ALTER TABLE `posts` DISABLE KEYS */;
INSERT INTO `posts` VALUES (1,0,1,1,0,0,'2014-01-01 00:00:01','my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1','richard.nixon@example.com','forumwithsufficientlylargename',0,0,2,1),(2,1,0,1,0,0,'2014-01-01 00:02:01','my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3my message 3','example2@mail.ru','forumwithsufficientlylargename',1,0,2,0),(3,2,0,1,1,0,'2014-01-02 00:02:01','my message 1','example4@mail.ru','forumwithsufficientlylargename',0,0,2,0),(4,0,1,0,0,0,'2014-01-03 00:01:01','my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1my message 1','example4@mail.ru','forum3',0,0,4,0),(5,0,0,0,0,0,'2014-01-03 00:08:01','my message 1','example4@mail.ru','forum3',0,0,3,0);
/*!40000 ALTER TABLE `posts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subscriptions`
--

DROP TABLE IF EXISTS `subscriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `subscriptions` (
  `user` varchar(64) DEFAULT NULL,
  `thread_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subscriptions`
--

LOCK TABLES `subscriptions` WRITE;
/*!40000 ALTER TABLE `subscriptions` DISABLE KEYS */;
INSERT INTO `subscriptions` VALUES ('richard.nixon@example.com',2),('example@mail.ru',2),('example2@mail.ru',1),('example4@mail.ru',3);
/*!40000 ALTER TABLE `subscriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `threads`
--

DROP TABLE IF EXISTS `threads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `threads` (
  `thread_id` int(11) NOT NULL AUTO_INCREMENT,
  `forum` varchar(64) DEFAULT NULL,
  `title` varchar(64) DEFAULT NULL,
  `isClosed` tinyint(1) DEFAULT NULL,
  `user` varchar(64) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `message` text,
  `slug` varchar(45) DEFAULT NULL,
  `isDeleted` tinyint(1) DEFAULT NULL,
  `likes` int(11) DEFAULT '0',
  `dislikes` int(11) DEFAULT '0',
  `posts` int(11) DEFAULT '0',
  PRIMARY KEY (`thread_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `threads`
--

LOCK TABLES `threads` WRITE;
/*!40000 ALTER TABLE `threads` DISABLE KEYS */;
INSERT INTO `threads` VALUES (1,'forumwithsufficientlylargename','Thread With Sufficiently Large Title',1,'richard.nixon@example.com','2014-01-01 00:00:01','hey hey hey hey!','Threadwithsufficientlylargetitle',1,0,0,0),(2,'forumwithsufficientlylargename','Thread I',0,'example@mail.ru','2013-12-31 00:01:01','hey!','thread1',0,0,0,3),(3,'forum3','Thread II',0,'example@mail.ru','2013-12-30 00:01:01','hey hey!','newslug',0,0,1,1),(4,'forum3','Тред Три',0,'example@mail.ru','2013-12-29 00:01:01','hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! hey hey hey! ','thread3',0,0,0,1);
/*!40000 ALTER TABLE `threads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(64) DEFAULT NULL,
  `about` text,
  `name` varchar(64) DEFAULT NULL,
  `email` varchar(64) DEFAULT NULL,
  `isAnonymous` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'user1','hello im user1','John','example@mail.ru',0),(2,'None','None','None','richard.nixon@example.com',1),(3,'user2','Wowowowow','NewName','example2@mail.ru',0),(4,'user3','Wowowowow!!!','NewName2','example3@mail.ru',0),(5,'user4','hello im user4','Jim','example4@mail.ru',0);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-10-31 10:36:21
