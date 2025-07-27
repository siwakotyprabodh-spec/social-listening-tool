-- Database setup for Social Listening Tool with user management

-- Create database
CREATE DATABASE IF NOT EXISTS social_listening;
USE social_listening;

-- Users table (existing)
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

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Crawl sessions table (user-specific)
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_name VARCHAR(100) NOT NULL,
    keywords JSON NOT NULL,
    search_logic ENUM('AND', 'OR') NOT NULL,
    date_from DATE NULL,
    date_to DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Crawl results table (user-specific)
CREATE TABLE IF NOT EXISTS crawl_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crawl_session_id INT NOT NULL,
    url VARCHAR(500) NOT NULL,
    date_found DATE NULL,
    raw_date VARCHAR(100) NULL,
    content TEXT NULL,
    summary TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crawl_session_id) REFERENCES crawl_sessions(id) ON DELETE CASCADE
);

-- User preferences table
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

-- Insert default admin user
INSERT IGNORE INTO users (username, password_hash, email, role) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8O', 'admin@example.com', 'admin');

-- Insert default user preferences for admin
INSERT IGNORE INTO user_preferences (user_id, translation_quality, summary_length) VALUES 
(1, 'Standard (Fast)', 'Medium (2 paragraphs)'); 