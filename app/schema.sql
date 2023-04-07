DROP TABLE IF EXISTS examples;
DROP TABLE IF EXISTS prompts;
DROP TABLE IF EXISTS metrics;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS exports;
DROP TABLE IF EXISTS styles;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS prompt_values;
DROP TABLE IF EXISTS style_keys;

CREATE TABLE examples (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `prompt_id` INTEGER,
  `completion` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tags (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `value` TEXT,
    `prompt_id` INTEGER,  /* Optional prompt association */
    `example_id` INTEGER  /* Optional example association */
);

CREATE TABLE prompts (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `style` INTEGER,
  `project_id` INTEGER,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prompt_values (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `prompt_id` INTEGER,
    `key` TEXT,
    `value` TEXT
);

CREATE TABLE styles (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `id_text` TEXT,  /* like 'instruct' or 'chat' */
    `project_id` INTEGER,
    `template` TEXT,
    `completion_key` TEXT,  /* Where the LLM is meant to add */
    `preview_key` TEXT,  /* For table previews of the prompts */
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE style_keys (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `name` TEXT,
    `style_id` INTEGER
);

CREATE TABLE projects (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `name` TEXT,
    `desc` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE metrics (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `score` TEXT,
  `example_id` INTEGER,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER,
  `type` TEXT,
  `pid` INTEGER,
  `status` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exports (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER,
  `filename` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO projects (`name`, `desc`)
VALUES ("Sample Project",
        "My first project"
        );

INSERT INTO styles (`id_text`, `project_id`, `template`, `completion_key`, `preview_key`)
VALUES ("instruct",
        1,
        "Instruction: {instruction}
Input: {input}
Output: {output}",
        "output",
        "instruction"
        );

INSERT INTO style_keys (`name`, `style_id`)
VALUES ("instruction",
        1
        );

INSERT INTO style_keys (`name`, `style_id`)
VALUES ("input",
        1
        );

INSERT INTO style_keys (`name`, `style_id`)
VALUES ("output",
        1
        );

INSERT INTO prompts (style, project_id)
VALUES (1,
        1
        );

INSERT INTO prompt_values (`prompt_id`, `key`, `value`)
VALUES (1,
        "instruction",
        "Write a line of Python that prints Hello World"
        );

INSERT INTO examples (prompt_id, completion)
VALUES (1,
        "print('Hello World')"
        );

INSERT INTO tags (`example_id`, `value`)
VALUES (1,
        "coding"
        );
