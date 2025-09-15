PRAGMA foreign_keys = ON;

-- USERS
CREATE TABLE IF NOT EXISTS users (
  user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  email       TEXT NOT NULL UNIQUE,
  pass_hash   TEXT NOT NULL,
  salt        TEXT NOT NULL,
  full_name   TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('customer','admin')),
  created_at  DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- CARS
CREATE TABLE IF NOT EXISTS cars (
  car_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  make          TEXT NOT NULL,
  model         TEXT NOT NULL,
  year          INTEGER NOT NULL,
  color         TEXT NOT NULL,
  mileage       INTEGER NOT NULL,
  daily_rate    REAL NOT NULL,
  available_now INTEGER NOT NULL DEFAULT 1,
  min_rent_days INTEGER NOT NULL DEFAULT 1,
  max_rent_days INTEGER NOT NULL DEFAULT 30
);

-- BOOKINGS
CREATE TABLE IF NOT EXISTS bookings (
  booking_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
  car_id      INTEGER NOT NULL REFERENCES cars(car_id) ON DELETE RESTRICT,
  start_date  DATE NOT NULL,
  end_date    DATE NOT NULL,
  rental_days INTEGER NOT NULL,
  total_fee   REAL NOT NULL,
  status      TEXT NOT NULL CHECK (status IN ('pending','approved','rejected')),
  created_at  DATETIME NOT NULL DEFAULT (datetime('now')),
  CHECK (julianday(end_date) > julianday(start_date))
);

-- BOOKING CHARGES
CREATE TABLE IF NOT EXISTS booking_charges (
  charge_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id  INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
  code        TEXT NOT NULL,
  amount      REAL NOT NULL
);

-- MAINTENANCE
CREATE TABLE IF NOT EXISTS maintenance (
  maint_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id      INTEGER NOT NULL REFERENCES cars(car_id) ON DELETE RESTRICT,
  type        TEXT NOT NULL,
  cost        REAL NOT NULL DEFAULT 0,
  start_date  DATE NOT NULL,
  end_date    DATE,
  notes       TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_bk_car_dates ON bookings(car_id, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_bk_car_dates_pa
  ON bookings(car_id, start_date, end_date)
  WHERE status IN ('pending','approved');
CREATE INDEX IF NOT EXISTS idx_m_car_dates ON maintenance(car_id, start_date, end_date);
