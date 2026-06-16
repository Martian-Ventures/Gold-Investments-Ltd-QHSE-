#!/usr/bin/env python
"""Initialize the database with raw SQL."""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Get database config
db_user = "root"
db_password = ""  # Empty password as in your config
db_host = "localhost"
db_name = "qhse_db"

print("Connecting to MySQL...")
try:
    # Connect to MySQL without selecting a specific database
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password if db_password else None,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    # Create database if it doesn't exist
    print(f"Creating database '{db_name}' if it doesn't exist...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    connection.commit()
    print(f"✓ Database '{db_name}' ready")
    
    # Select the database
    cursor.execute(f"USE {db_name};")
    
    print("\nCreating tables...")
    
    # Create roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `roles` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `name` VARCHAR(64) NOT NULL UNIQUE,
            `description` VARCHAR(255),
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'roles' table")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `full_name` VARCHAR(120) NOT NULL UNIQUE,
            `email` VARCHAR(120) NOT NULL UNIQUE,
            `password_hash` VARCHAR(255) NOT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `role` ENUM('admin', 'auditor', 'employee') DEFAULT 'employee',
            `is_active` BOOLEAN DEFAULT TRUE,
            `twofa_secret` VARCHAR(32),
            PRIMARY KEY (`id`),
            UNIQUE KEY `ix_users_email` (`email`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'users' table")
    
    # Create user_roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `user_roles` (
            `user_id` INT NOT NULL,
            `role_id` INT NOT NULL,
            PRIMARY KEY (`user_id`, `role_id`),
            FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
            FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'user_roles' table")
    
    # Create incidents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `incidents` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `title` VARCHAR(255) NOT NULL,
            `department` VARCHAR(128),
            `category` VARCHAR(64),
            `type` VARCHAR(64),
            `severity` VARCHAR(32),
            `description` LONGTEXT,
            `employees_affected` INT DEFAULT 0,
            `hours_per_employee` FLOAT DEFAULT 0,
            `idle_time_hours` FLOAT DEFAULT 0,
            `hours_lost` FLOAT DEFAULT 0,
            `cost_per_hour` FLOAT DEFAULT 0,
            `total_cost` FLOAT DEFAULT 0,
            `investigator_id` INT,
            `incident_datetime` DATETIME,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `reported_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `created_by_id` INT,
            `status` VARCHAR(32) DEFAULT 'Reported',
            PRIMARY KEY (`id`),
            FOREIGN KEY (`investigator_id`) REFERENCES `users` (`id`),
            FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'incidents' table")
    
    # Create incident_updates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `incident_updates` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `incident_id` INT,
            `update_text` LONGTEXT NOT NULL,
            `updated_by_id` INT,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            FOREIGN KEY (`incident_id`) REFERENCES `incidents` (`id`),
            FOREIGN KEY (`updated_by_id`) REFERENCES `users` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'incident_updates' table")
    
    # Create capas table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `capas` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `incident_id` INT,
            `action` VARCHAR(500),
            `owner` VARCHAR(255),
            `due_date` DATE,
            `status` VARCHAR(64) DEFAULT 'Open',
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            FOREIGN KEY (`incident_id`) REFERENCES `incidents` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'capas' table")
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `documents` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `title` VARCHAR(255),
            `filename` VARCHAR(255),
            `uploaded_by_id` INT,
            `uploaded_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            FOREIGN KEY (`uploaded_by_id`) REFERENCES `users` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'documents' table")
    
    # Create audits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `audits` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `organization` VARCHAR(255),
            `standard` VARCHAR(255),
            `plan_date` DATE,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("✓ Created 'audits' table")
    
    connection.commit()
    print("\n✅ All tables created successfully!")
    
    # Add admin user directly via SQL
    print("\nCreating default admin user...")
    from werkzeug.security import generate_password_hash
    
    admin_password_hash = generate_password_hash("AdminPass123!")
    
    cursor.execute("""
        INSERT IGNORE INTO `users` (full_name, email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, %s)
    """, ("Administrator", "admin@example.com", admin_password_hash, "admin", True))
    
    connection.commit()
    
    if cursor.rowcount > 0:
        print("✓ Created default admin user")
        print("  Email: admin@example.com")
        print("  Password: AdminPass123!")
    else:
        print("⚠ Admin user already exists")
    
    cursor.close()
    connection.close()
    print("\n✅ Database initialization complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    raise
