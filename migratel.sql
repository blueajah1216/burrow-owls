-- 1) Add finished_date column if it doesn't exist
-- SQLite doesn't support "ADD COLUMN IF NOT EXISTS" reliably in older versions,
-- so we handle it by attempting and ignoring errors manually when running.
ALTER TABLE reviews ADD COLUMN finished_date DATE;

-- 2) Create book_metadata table
CREATE TABLE IF NOT EXISTS book_metadata (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_slug VARCHAR(200) NOT NULL,
  title VARCHAR(300) NOT NULL,
  author VARCHAR(300),
  cover_url VARCHAR(500),
  summary TEXT,
  source VARCHAR(100),
  updated_at DATETIME
);

-- 3) Add unique index for book_slug
CREATE UNIQUE INDEX IF NOT EXISTS idx_book_metadata_book_slug
  ON book_metadata(book_slug);

-- 4) (Optional but useful) indexes for reviews
CREATE INDEX IF NOT EXISTS idx_reviews_person ON reviews(person);
CREATE INDEX IF NOT EXISTS idx_reviews_book_slug ON reviews(book_slug);