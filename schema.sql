-- EngineerOS Database Schema
-- Run this in phpMyAdmin after creating the 'engineeros_db' database

CREATE DATABASE IF NOT EXISTS engineeros_db;
USE engineeros_db;

-- Table to store user authentication and basic details
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table to store detailed user profiles for the career OS
CREATE TABLE profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    college VARCHAR(200),
    branch VARCHAR(100),
    year TINYINT,
    semester TINYINT,
    cgpa DECIMAL(4,2),
    target_role VARCHAR(100),
    target_companies TEXT,
    preferred_domain VARCHAR(100),
    career_timeline VARCHAR(50),
    github_url VARCHAR(255),
    linkedin_url VARCHAR(255),
    leetcode_url VARCHAR(255),
    completion_percentage INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table to store user skills
CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    level ENUM('beginner','intermediate','advanced') DEFAULT 'beginner',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY (user_id, name)
);

-- Table to store user interests
CREATE TABLE interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY (user_id, name)
);

-- Table to store generated roadmaps
CREATE TABLE roadmaps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    target_role VARCHAR(100),
    estimated_duration VARCHAR(50),
    strong_areas TEXT,
    gaps_identified TEXT,
    overall_readiness INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX (user_id, is_active)
);

-- Table to store phases of a roadmap
CREATE TABLE roadmap_phases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roadmap_id INT NOT NULL,
    phase_number TINYINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    duration VARCHAR(50),
    status ENUM('not_started','in_progress','completed') DEFAULT 'not_started',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (roadmap_id) REFERENCES roadmaps(id) ON DELETE CASCADE,
    UNIQUE KEY (roadmap_id, phase_number)
);

-- Table to store milestones within a roadmap phase
CREATE TABLE milestones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phase_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status ENUM('not_started','in_progress','completed') DEFAULT 'not_started',
    milestone_type ENUM('learning','project','practice','assessment') DEFAULT 'learning',
    resources JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES roadmap_phases(id) ON DELETE CASCADE
);

-- Table to store user progress tracking
CREATE TABLE progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    roadmap_id INT,
    milestone_id INT,
    type ENUM('milestone_completed','skill_added','project_completed','course_completed') NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    skills_gained TEXT,
    readiness_before INT,
    readiness_after INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (roadmap_id) REFERENCES roadmaps(id) ON DELETE SET NULL,
    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE SET NULL,
    INDEX (user_id, created_at)
);
