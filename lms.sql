-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema lms_db
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema lms_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `lms_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `lms_db` ;

-- -----------------------------------------------------
-- Table `lms_db`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`users` (
  `created_at` DATETIME(6) NULL DEFAULT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('ADMIN', 'STUDENT', 'TEACHER') NOT NULL,
  `username` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `UK6dotkott2kjsp8vw4d0m25fb7` (`email` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`courses`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`courses` (
  `end_date` DATE NULL DEFAULT NULL,
  `start_date` DATE NULL DEFAULT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `instructor_id` BIGINT NOT NULL,
  `description` TEXT NULL DEFAULT NULL,
  `title` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FKcyfum8goa6q5u13uog0563gyp` (`instructor_id` ASC) VISIBLE,
  CONSTRAINT `FKcyfum8goa6q5u13uog0563gyp`
    FOREIGN KEY (`instructor_id`)
    REFERENCES `lms_db`.`users` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`quizzes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`quizzes` (
  `total_marks` INT NOT NULL,
  `course_id` BIGINT NOT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FKpxdnhxeppxx606nhyjtjyharp` (`course_id` ASC) VISIBLE,
  CONSTRAINT `FKpxdnhxeppxx606nhyjtjyharp`
    FOREIGN KEY (`course_id`)
    REFERENCES `lms_db`.`courses` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`questions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`questions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `quiz_id` BIGINT NOT NULL,
  `correct_answer` VARCHAR(255) NULL DEFAULT NULL,
  `options` TEXT NULL DEFAULT NULL,
  `question_text` TEXT NOT NULL,
  `question_type` ENUM('MULTIPLE_CHOICE', 'SHORT_ANSWER', 'TRUE_FALSE') NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FKn3gvco4b0kewxc0bywf1igfms` (`quiz_id` ASC) VISIBLE,
  CONSTRAINT `FKn3gvco4b0kewxc0bywf1igfms`
    FOREIGN KEY (`quiz_id`)
    REFERENCES `lms_db`.`quizzes` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 26
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`answers`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`answers` (
  `is_correct` BIT(1) NULL DEFAULT NULL,
  `marks_obtained` DOUBLE NULL DEFAULT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `question_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `answer_text` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FK3erw1a3t0r78st8ty27x6v3g1` (`question_id` ASC) VISIBLE,
  INDEX `FK5bp3d5loftq2vjn683ephn75a` (`user_id` ASC) VISIBLE,
  CONSTRAINT `FK3erw1a3t0r78st8ty27x6v3g1`
    FOREIGN KEY (`question_id`)
    REFERENCES `lms_db`.`questions` (`id`),
  CONSTRAINT `FK5bp3d5loftq2vjn683ephn75a`
    FOREIGN KEY (`user_id`)
    REFERENCES `lms_db`.`users` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`certificates`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`certificates` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `certificate_code` VARCHAR(255) NOT NULL,
  `issue_date` DATETIME(6) NOT NULL,
  `course_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `UKilkogva3i6dm8ngpqipamo70y` (`certificate_code` ASC) VISIBLE,
  INDEX `FKs5rftqrsgkog7h4piv3f7a9s6` (`course_id` ASC) VISIBLE,
  INDEX `FKd3f6enpb3p3xovee9klklf05r` (`user_id` ASC) VISIBLE,
  CONSTRAINT `FKd3f6enpb3p3xovee9klklf05r`
    FOREIGN KEY (`user_id`)
    REFERENCES `lms_db`.`users` (`id`),
  CONSTRAINT `FKs5rftqrsgkog7h4piv3f7a9s6`
    FOREIGN KEY (`course_id`)
    REFERENCES `lms_db`.`courses` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`enrollments`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`enrollments` (
  `course_id` BIGINT NOT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `status` ENUM('COMPLETED', 'DROPPED', 'ENROLLED') NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FKho8mcicp4196ebpltdn9wl6co` (`course_id` ASC) VISIBLE,
  INDEX `FK3hjx6rcnbmfw368sxigrpfpx0` (`user_id` ASC) VISIBLE,
  CONSTRAINT `FK3hjx6rcnbmfw368sxigrpfpx0`
    FOREIGN KEY (`user_id`)
    REFERENCES `lms_db`.`users` (`id`),
  CONSTRAINT `FKho8mcicp4196ebpltdn9wl6co`
    FOREIGN KEY (`course_id`)
    REFERENCES `lms_db`.`courses` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 7
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`lessons`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`lessons` (
  `course_id` BIGINT NOT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `content` TEXT NULL DEFAULT NULL,
  `title` VARCHAR(255) NOT NULL,
  `video_url` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `FK17ucc7gjfjddsyi0gvstkqeat` (`course_id` ASC) VISIBLE,
  CONSTRAINT `FK17ucc7gjfjddsyi0gvstkqeat`
    FOREIGN KEY (`course_id`)
    REFERENCES `lms_db`.`courses` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 26
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`notifications`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`notifications` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `message` TEXT NOT NULL,
  `is_read` BIT(1) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `type` ENUM('CERTIFICATE_ISSUED', 'COURSE_COMPLETED', 'ENROLLMENT', 'GENERAL', 'LESSON_ADDED', 'QUIZ_GRADED') NOT NULL,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FK9y21adhxn0ayjhfocscqox7bh` (`user_id` ASC) VISIBLE,
  CONSTRAINT `FK9y21adhxn0ayjhfocscqox7bh`
    FOREIGN KEY (`user_id`)
    REFERENCES `lms_db`.`users` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `lms_db`.`progress`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lms_db`.`progress` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `last_accessed` DATETIME(6) NULL DEFAULT NULL,
  `lesson_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `status` ENUM('COMPLETED', 'IN_PROGRESS', 'NOT_STARTED') NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `FKl0j4exxbrn12496b20t6o1kb3` (`lesson_id` ASC) VISIBLE,
  INDEX `FK7fyumbty8qgbd7sfbbjnqdo62` (`user_id` ASC) VISIBLE,
  CONSTRAINT `FK7fyumbty8qgbd7sfbbjnqdo62`
    FOREIGN KEY (`user_id`)
    REFERENCES `lms_db`.`users` (`id`),
  CONSTRAINT `FKl0j4exxbrn12496b20t6o1kb3`
    FOREIGN KEY (`lesson_id`)
    REFERENCES `lms_db`.`lessons` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
