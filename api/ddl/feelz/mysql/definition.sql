CREATE TABLE IF NOT EXISTS `feelz`.`diary` (
  `id` BIGINT AUTO_INCREMENT,
  `entity_id` BIGINT,
  `when` BIGINT,
  `what` JSON NOT NULL,
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `when` (`when`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`dispute` (
  `id` BIGINT AUTO_INCREMENT,
  `from_id` BIGINT,
  `to_id` BIGINT,
  `when` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `from_id_to_id_when` (`from_id`,`to_id`,`when`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`fam` (
  `id` BIGINT AUTO_INCREMENT,
  `from_id` BIGINT,
  `to_id` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `from_id_to_id` (`from_id`,`to_id`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`mediation` (
  `id` BIGINT AUTO_INCREMENT,
  `dispute_id` BIGINT,
  `entity_id` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `dispute_id_entity_id` (`dispute_id`,`entity_id`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`mood` (
  `id` BIGINT AUTO_INCREMENT,
  `entity_id` BIGINT,
  `when` BIGINT,
  `what` VARCHAR(255) NOT NULL,
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `when` (`when`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`muy_bien` (
  `id` BIGINT AUTO_INCREMENT,
  `entity_id` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `when` BIGINT,
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `entity_id` (`entity_id`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`que_pasa` (
  `id` BIGINT AUTO_INCREMENT,
  `entity_id` BIGINT,
  `when_min` BIGINT,
  `when_max` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `entity_id` (`entity_id`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`que_pasa_check` (
  `id` BIGINT AUTO_INCREMENT,
  `entity_id` BIGINT,
  `when` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `when` (`when`),
  UNIQUE `entity_id_when` (`entity_id`,`when`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`state` (
  `id` BIGINT AUTO_INCREMENT,
  `entity_id` BIGINT,
  `when` BIGINT,
  `what` VARCHAR(255) NOT NULL DEFAULT 'unable',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `when` (`when`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`ugood` (
  `id` BIGINT AUTO_INCREMENT,
  `from_id` BIGINT,
  `to_id` BIGINT,
  `when_min` BIGINT,
  `when_max` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `from_id_to_id` (`from_id`,`to_id`)
);

CREATE TABLE IF NOT EXISTS `feelz`.`ugood_check` (
  `id` BIGINT AUTO_INCREMENT,
  `from_id` BIGINT,
  `to_id` BIGINT,
  `when` BIGINT,
  `status` VARCHAR(255) NOT NULL DEFAULT 'requested',
  `meta` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `when` (`when`),
  UNIQUE `from_id_to_id_when` (`from_id`,`to_id`,`when`)
);
