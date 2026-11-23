-- ============================================================
-- Web-Based Library Management System
-- Database: library_db  (MySQL)
-- Matches the ER design / data structures in Chapter 3 of the report
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- ---------------------------------------------------------------
-- 1. Admin
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Admin (
    Admin_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Name       VARCHAR(100) NOT NULL,
    Email      VARCHAR(120) NOT NULL UNIQUE,
    Password   VARCHAR(255) NOT NULL   -- stored as a hash, never plain text
);

-- ---------------------------------------------------------------
-- 2. Member
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Member (
    Member_ID  INT AUTO_INCREMENT PRIMARY KEY,
    Name       VARCHAR(100) NOT NULL,
    Email      VARCHAR(120) NOT NULL UNIQUE,
    Phone      VARCHAR(20),
    Password   VARCHAR(255) NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- 3. Category
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Category (
    Category_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Category_Name VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------
-- 4. Book
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Book (
    Book_ID     INT AUTO_INCREMENT PRIMARY KEY,
    ISBN        VARCHAR(20) NOT NULL UNIQUE,
    Title       VARCHAR(200) NOT NULL,
    Author      VARCHAR(150) NOT NULL,
    Status      VARCHAR(20) NOT NULL DEFAULT 'Available', -- Available / Borrowed
    Category_ID INT,
    FOREIGN KEY (Category_ID) REFERENCES Category(Category_ID) ON DELETE SET NULL
);

-- ---------------------------------------------------------------
-- 5. Borrowing
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Borrowing (
    Borrow_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Member_ID   INT NOT NULL,
    Book_ID     INT NOT NULL,
    Borrow_Date DATE NOT NULL,
    Due_Date    DATE NOT NULL,
    Return_Date DATE NULL,
    Status      VARCHAR(20) NOT NULL DEFAULT 'Borrowed', -- Borrowed / Returned
    FOREIGN KEY (Member_ID) REFERENCES Member(Member_ID) ON DELETE CASCADE,
    FOREIGN KEY (Book_ID) REFERENCES Book(Book_ID) ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- 6. Fine
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Fine (
    Fine_ID     INT AUTO_INCREMENT PRIMARY KEY,
    Borrow_ID   INT NOT NULL,
    Amount      DECIMAL(8,2) NOT NULL,
    Issue_Date  DATE NOT NULL,
    Paid_Status VARCHAR(20) NOT NULL DEFAULT 'Unpaid', -- Paid / Unpaid
    FOREIGN KEY (Borrow_ID) REFERENCES Borrowing(Borrow_ID) ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- 7. Chatbot_Query
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Chatbot_Query (
    Query_ID    INT AUTO_INCREMENT PRIMARY KEY,
    Member_ID   INT,
    Question    TEXT NOT NULL,
    Response    TEXT NOT NULL,
    Query_Date  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Member_ID) REFERENCES Member(Member_ID) ON DELETE SET NULL
);

-- ---------------------------------------------------------------
-- Seed data (optional, useful for demo / viva)
-- ---------------------------------------------------------------
INSERT INTO Admin (Name, Email, Password) VALUES
-- password = 'admin123' (hashed at first run by seed.py instead of here)
('Library Admin', 'admin@library.com', 'REPLACED_BY_SEED_SCRIPT');

INSERT INTO Category (Category_Name) VALUES
('Fiction'), ('Non-Fiction'), ('Science'), ('Technology'), ('History'), ('Children');

INSERT INTO Book (ISBN, Title, Author, Status, Category_ID) VALUES
('978-0134685991', 'Effective Java', 'Joshua Bloch', 'Available', 4),
('978-0132350884', 'Clean Code', 'Robert C. Martin', 'Available', 4),
('978-0439708180', 'Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', 'Available', 1),
('978-0451524935', '1984', 'George Orwell', 'Available', 1),
('978-0062316097', 'Sapiens', 'Yuval Noah Harari', 'Available', 2),
('978-0553380163', 'A Brief History of Time', 'Stephen Hawking', 'Available', 3),
('978-0393609394', 'Astrophysics for People in a Hurry', 'Neil deGrasse Tyson', 'Available', 3),
('978-0141439600', 'Pride and Prejudice', 'Jane Austen', 'Available', 1);
