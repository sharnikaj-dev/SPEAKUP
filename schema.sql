-- =============================================================================
-- SPEAKUP: Conversational English Practice Platform
-- Database Schema Definition
-- =============================================================================

-- Create database if it does not already exist
CREATE DATABASE IF NOT EXISTS speakup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE speakup;

-- -----------------------------------------------------------------------------
-- 1. Users Table
-- Stores user accounts, authentication credentials, and system roles.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(191) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 2. Levels Table
-- Stores difficulty levels for learners (e.g., Level 1: Beginner, Level 2: Intermediate).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS levels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level_number INT NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description TEXT
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 3. Profiles Table
-- Stores learner preferences, background, and current assigned level.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    native_language VARCHAR(50),
    background VARCHAR(100),
    goal VARCHAR(255),
    current_level_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_profiles_level FOREIGN KEY (current_level_id) 
        REFERENCES levels(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 4. Scenarios Table
-- Practice scenarios mapped to levels with AI persona prompts and opening messages.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    ai_role_prompt TEXT,
    opening_message TEXT,
    CONSTRAINT fk_scenarios_level FOREIGN KEY (level_id) 
        REFERENCES levels(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 5. Conversations Table
-- Tracks a dialogue session between a learner and an AI scenario.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    scenario_id INT NOT NULL,
    status ENUM('active', 'completed') NOT NULL DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    CONSTRAINT fk_conversations_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_conversations_scenario FOREIGN KEY (scenario_id) 
        REFERENCES scenarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 6. Messages Table
-- Stores individual chat messages sent by both user and AI.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender ENUM('user', 'ai') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) 
        REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 7. Feedback Table
-- Stores AI corrections and multi-lingual explanations for learner messages.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message_id INT NOT NULL,
    corrected_sentence TEXT,
    explanation TEXT,
    native_explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_message FOREIGN KEY (message_id) 
        REFERENCES messages(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 8. Mistakes Table
-- Logs specific language mistakes per learner session for review and analytics.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mistakes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    conversation_id INT NOT NULL,
    mistake_type ENUM('grammar', 'vocabulary', 'sentence', 'fluency') NOT NULL,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mistakes_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_mistakes_conversation FOREIGN KEY (conversation_id) 
        REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 9. Progress Table
-- Tracks unlocked and completed status for each user across levels.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    level_id INT NOT NULL,
    status ENUM('locked', 'unlocked', 'completed') NOT NULL DEFAULT 'locked',
    completed_at TIMESTAMP NULL,
    UNIQUE KEY unique_user_level (user_id, level_id),
    CONSTRAINT fk_progress_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_progress_level FOREIGN KEY (level_id) 
        REFERENCES levels(id) ON DELETE CASCADE
) ENGINE=InnoDB;
