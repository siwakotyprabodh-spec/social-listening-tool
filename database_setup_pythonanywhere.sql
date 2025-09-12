-- Database setup for Social Listening Tool on PythonAnywhere
-- Use existing database: sociallisten$default

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
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

-- Crawl results table
CREATE TABLE IF NOT EXISTS crawl_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL,
    title VARCHAR(500),
    content LONGTEXT,
    date DATE,
    keyword VARCHAR(100),
    sentiment JSON,
    translation TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password_hash, email, role) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J8K8K8K8K', 'admin@example.com', 'admin')
ON DUPLICATE KEY UPDATE username=username;
