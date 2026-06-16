#!/usr/bin/env python
"""Initialize the database with MyISAM tables."""

import pymysql
from werkzeug.security import generate_password_hash

db_user = "root"
db_password = ""
db_host = "localhost"
db_name = "qhse_db"

print("Connecting to MySQL...")
connection = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password if db_password else None,
    database=db_name,
    charset='utf8mb4'
)

cursor = connection.cursor()

print("\nCreating tables...")

# Create roles table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(64) NOT NULL UNIQUE,
        description VARCHAR(255)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'roles' table")

# Create users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(120) NOT NULL UNIQUE,
        email VARCHAR(120) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        role ENUM('admin', 'auditor', 'employee') DEFAULT 'employee',
        is_active BOOLEAN DEFAULT TRUE,
        twofa_secret VARCHAR(32),
        KEY ix_users_email (email)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'users' table")

# Create user_roles table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INT NOT NULL,
        role_id INT NOT NULL,
        PRIMARY KEY (user_id, role_id)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'user_roles' table")

# Create incidents table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        department VARCHAR(128),
        category VARCHAR(64),
        type VARCHAR(64),
        severity VARCHAR(32),
        description LONGTEXT,
        employees_affected INT DEFAULT 0,
        hours_per_employee FLOAT DEFAULT 0,
        idle_time_hours FLOAT DEFAULT 0,
        hours_lost FLOAT DEFAULT 0,
        cost_per_hour FLOAT DEFAULT 0,
        total_cost FLOAT DEFAULT 0,
        investigator_id INT,
        incident_datetime DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_id INT,
        status VARCHAR(32) DEFAULT 'Reported'
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'incidents' table")

# Create incident_updates table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS incident_updates (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        incident_id INT,
        update_text LONGTEXT NOT NULL,
        updated_by_id INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'incident_updates' table")

# Create capas table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS capas (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        incident_id INT,
        action VARCHAR(500),
        owner VARCHAR(255),
        due_date DATE,
        status VARCHAR(64) DEFAULT 'Open',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'capas' table")

# Create documents table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        filename VARCHAR(255),
        uploaded_by_id INT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'documents' table")

# Create audits table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS audits (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        organization VARCHAR(255),
        standard VARCHAR(255),
        plan_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'audits' table")

# Create alembic_version table for migration tracking
cursor.execute("""
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) PRIMARY KEY
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;
""")
print("✓ Created 'alembic_version' table")

connection.commit()
print("\n✅ All tables created successfully!")

# Add admin user
print("\nCreating default admin user...")
admin_password_hash = generate_password_hash("AdminPass123!")

try:
    cursor.execute("""
        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, %s)
    """, ("Administrator", "admin@example.com", admin_password_hash, "admin", True))
    connection.commit()
    
    if cursor.rowcount > 0:
        print("✓ Created default admin user")
        print("  Email: admin@example.com")
        print("  Password: AdminPass123!")
except pymysql.IntegrityError:
    print("⚠ Admin user already exists")
    connection.rollback()

cursor.close()
connection.close()

print("\n✅ Database initialization complete!")
