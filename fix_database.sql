-- Fix database structure for Social Listening Tool

-- Use the database
USE social_listening;

-- Check if users table exists, if not create it
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'user', 'premium') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Add role column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS role ENUM('admin', 'user', 'premium') DEFAULT 'user' AFTER email;

-- Add is_active column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE AFTER role;

-- Add created_at column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER is_active;

-- Add last_login column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP NULL AFTER created_at;

-- Create user_sessions table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create user_preferences table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    translation_quality ENUM('Standard (Fast)', 'High Quality (Slower)', 'Best Quality (Slowest)') DEFAULT 'Standard (Fast)',
    summary_length ENUM('Short (1 paragraph)', 'Medium (2 paragraphs)', 'Long (3+ paragraphs)') DEFAULT 'Medium (2 paragraphs)',
    max_crawl_pages INT DEFAULT 100,
    crawl_timeout INT DEFAULT 120,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert default admin user if not exists
INSERT IGNORE INTO users (username, password_hash, email, role) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8O', 'admin@example.com', 'admin');

-- Insert default user preferences for admin if not exists
INSERT IGNORE INTO user_preferences (user_id, translation_quality, summary_length) VALUES 
(1, 'Standard (Fast)', 'Medium (2 paragraphs)'); 