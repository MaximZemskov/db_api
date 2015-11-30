

SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT ;
SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS ;
SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION ;
SET NAMES utf8 ;
SET @OLD_TIME_ZONE=@@TIME_ZONE ;
SET TIME_ZONE='+00:00';
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 ;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 ;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' ;
SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;


DROP TABLE IF EXISTS `users`;

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




DROP TABLE IF EXISTS `forums`;

CREATE TABLE `forums` (
  `name` varchar(64) DEFAULT NULL,
  `short_name` varchar(64) DEFAULT NULL,
  `user` varchar(64) DEFAULT NULL,
  `forum_id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`forum_id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  UNIQUE KEY `short_name_UNIQUE` (`short_name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;



DROP TABLE IF EXISTS `followers`;

CREATE TABLE `followers` (
  `who_user` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  `whom_user` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  UNIQUE INDEX `main` (`who_user`, `whom_user`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;




DROP TABLE IF EXISTS `posts`;

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
  PRIMARY KEY (`post_id`),
  INDEX `f-u_idx` (`forum`, `user`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;



DROP TABLE IF EXISTS `subscriptions`;

CREATE TABLE `subscriptions` (
  `user` varchar(64) DEFAULT NULL,
  `thread_id` int(11) DEFAULT NULL,
  UNIQUE INDEX `u-t_idx` (`user`, `thread_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



DROP TABLE IF EXISTS `threads`;

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




SET TIME_ZONE=@OLD_TIME_ZONE ;

SET SQL_MODE=@OLD_SQL_MODE ;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS ;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS ;
SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT ;
SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS ;
SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION ;
SET SQL_NOTES=@OLD_SQL_NOTES ;

