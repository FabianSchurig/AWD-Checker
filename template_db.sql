BEGIN TRANSACTION;
CREATE TABLE "Users" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`chat_id`	TEXT,
	`is_admin`	INTEGER NOT NULL
);
CREATE TABLE "Track" (
	`item_id`	INTEGER NOT NULL,
	`user_id`	INTEGER NOT NULL,
	`target_amount`	INTEGER,
	FOREIGN KEY(`item_id`) REFERENCES `Items`(`id`),
	FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`),
	PRIMARY KEY(`user_id`, `item_id`)
);
CREATE TABLE "Prices" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`item_id`	INTEGER,
	`condition`	INTEGER,
	`amount`	INTEGER,
	`created_at`	TIMESTAMP,
	`currency_code`	TEXT,
	FOREIGN KEY(`item_id`) REFERENCES `Items`(`id`)
);
CREATE TABLE "Items" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`asin`	TEXT,
	`url`	TEXT
);
COMMIT;
