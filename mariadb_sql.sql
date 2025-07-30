CREATE TABLE `staff` (
  `staff_id` varchar(255) PRIMARY KEY,
  `name` varchar(255),
  `position` varchar(255),
  `team_id` int,
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `team` (
  `team_id` integer PRIMARY KEY,
  `team_name` varchar(255)
);

CREATE TABLE `shift_code` (
  `shift_code` char(1) PRIMARY KEY,
  `description` varchar(255)
);

CREATE TABLE `schedule` (
  `schedule_id` integer PRIMARY KEY,
  `staff_id` varchar(255),
  `schedule_data` text,
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `duty_schedule` (
  `id` integer PRIMARY KEY,
  `staff_id` varchar(255),
  `duty_date` date,
  `shift_code` char(1),
  `work_time` varchar(255),
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `team_constraint` (
  `id` integer PRIMARY KEY,
  `team_id` integer,
  `constraint_type` varchar(255),
  `param_1` varchar(255),
  `weight_point` integer,
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `shift_constraint_rule` (
  `id` integer PRIMARY KEY,
  `shift_code_before` char(1),
  `shift_code_after` char(1),
  `constraint_type` varchar(255),
  `description` varchar(255),
  `weight_point` integer,
  `created_at` timestamp,
  `updated_at` timestamp
);

-- ALTER TABLE `staff` ADD FOREIGN KEY (`team_id`) REFERENCES `team` (`team_id`);

-- ALTER TABLE `schedule` ADD FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`);

-- ALTER TABLE `duty_schedule` ADD FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`);

-- ALTER TABLE `duty_schedule` ADD FOREIGN KEY (`shift_code`) REFERENCES `shift_code` (`shift_code`);

-- ALTER TABLE `team_constraint` ADD FOREIGN KEY (`team_id`) REFERENCES `team` (`team_id`);

-- ALTER TABLE `shift_constraint_rule` ADD FOREIGN KEY (`shift_code_before`) REFERENCES `shift_code` (`shift_code`);

-- ALTER TABLE `shift_constraint_rule` ADD FOREIGN KEY (`shift_code_after`) REFERENCES `shift_code` (`shift_code`);
