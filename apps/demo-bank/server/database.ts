import Database from 'better-sqlite3';
import path from 'path';
import { existsSync, mkdirSync } from 'fs';

const dbDir = path.join(process.cwd(), 'data');
if (!existsSync(dbDir)) {
  mkdirSync(dbDir, { recursive: true });
}

const dbPath = path.join(dbDir, 'demo-bank.db');
const db = new Database(dbPath);

// Habilitar foreign keys
db.pragma('foreign_keys = ON');

// Crear tablas
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    rut TEXT UNIQUE NOT NULL,
    balance REAL DEFAULT 0,
    account_number TEXT UNIQUE NOT NULL,
    transfer_pin TEXT DEFAULT NULL,
    biometric_user_id TEXT,
    enrollment_id TEXT,
    is_voice_enrolled INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    rut TEXT NOT NULL,
    email TEXT,
    bank_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    account_number TEXT NOT NULL,
    is_favorite INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    recipient_first_name TEXT,
    recipient_last_name TEXT,
    recipient_rut TEXT,
    recipient_email TEXT,
    recipient_bank TEXT,
    recipient_account_type TEXT,
    recipient_account_number TEXT,
    description TEXT,
    status TEXT DEFAULT 'completed',
    verification_method TEXT,
    verification_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
  CREATE INDEX IF NOT EXISTS idx_users_biometric_id ON users(biometric_user_id);
  CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
  CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
  CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id);
`);

// Insertar usuarios reales de la familia si no existen
const seedUsers = db.prepare(`
  INSERT OR IGNORE INTO users (
    id, email, password, first_name, last_name, rut, 
    balance, account_number, transfer_pin, biometric_user_id, is_voice_enrolled
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

// Usuarios reales de Banco Familia (datos de la API biométrica)
// Usuario 1 - Tomás Poblete (admin del banco)
seedUsers.run(
  '24ad81e4-363f-44ef-b87b-207c5b53213d',
  'ft.fernandotomas@gmail.com',
  'tomas123',
  'Tomás',
  'Poblete',
  '20904540-0',
  2500000,
  '0001234567',
  null,
  '24ad81e4-363f-44ef-b87b-207c5b53213d',
  1
);

// Usuario 2 - Pia Poblete
seedUsers.run(
  '33097117-40b9-4f9c-a16f-261cba278e2b',
  'piapobletech@gmail.com',
  'pia123',
  'Pia',
  'Poblete',
  '18572849-8',
  1200000,
  '0001234568',
  null,
  '33097117-40b9-4f9c-a16f-261cba278e2b',
  1
);

// Usuario 3 - Ana Chamorro
seedUsers.run(
  'fa64f420-c36a-4abf-b8ea-c9aad297fe47',
  'anachamorromunoz@gmail.com',
  'ana123',
  'Ana',
  'Chamorro',
  '9555737-6',
  1500000,
  '0001234569',
  null,
  'fa64f420-c36a-4abf-b8ea-c9aad297fe47',
  1
);

// Usuario 4 - Raul Poblete
seedUsers.run(
  '7f43c9a6-50a9-449a-bec7-9473cf3fb05f',
  'rapomo3@gmail.com',
  'raul123',
  'Raul',
  'Poblete',
  '8385075-2',
  1800000,
  '0001234570',
  null,
  '7f43c9a6-50a9-449a-bec7-9473cf3fb05f',
  1
);

// Usuario 5 - Matias Oliva
seedUsers.run(
  'efb433f2-cb7f-4b16-b3b7-f63a04de38a0',
  'maolivautal@gmail.com',
  'matias123',
  'Matias',
  'Oliva',
  '21016246-1',
  900000,
  '0001234571',
  null,
  'efb433f2-cb7f-4b16-b3b7-f63a04de38a0',
  1
);

// Usuario 6 - Ignacio Norambuena
seedUsers.run(
  '6c8e24d8-5e5a-425c-984c-226be3b92c1e',
  'ignacio.norambuena1990@gmail.com',
  'ignacio123',
  'Ignacio',
  'Norambuena',
  '21013703-3',
  750000,
  '0001234572',
  null,
  '6c8e24d8-5e5a-425c-984c-226be3b92c1e',
  1
);

// Insertar contactos demo
const seedContacts = db.prepare(`
  INSERT OR IGNORE INTO contacts (
    user_id, first_name, last_name, rut, email, bank_name, account_type, account_number, is_favorite
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

// Contactos para Tomás (los demás miembros de la familia)
seedContacts.run('24ad81e4-363f-44ef-b87b-207c5b53213d', 'Pia', 'Poblete', '18.572.849-8', 'piapobletech@gmail.com', 'Banco Familia', 'Cuenta Corriente', '0001234568', 1);
seedContacts.run('24ad81e4-363f-44ef-b87b-207c5b53213d', 'Ana', 'Chamorro', '9.555.737-6', 'anachamorromunoz@gmail.com', 'Banco Familia', 'Cuenta Corriente', '0001234569', 1);
seedContacts.run('24ad81e4-363f-44ef-b87b-207c5b53213d', 'Raul', 'Poblete', '8.385.075-2', 'rapomo3@gmail.com', 'Banco Familia', 'Cuenta Corriente', '0001234570', 1);
seedContacts.run('24ad81e4-363f-44ef-b87b-207c5b53213d', 'Matias', 'Oliva', '21.016.246-1', 'maolivautal@gmail.com', 'Banco Familia', 'Cuenta Corriente', '0001234571', 0);
seedContacts.run('24ad81e4-363f-44ef-b87b-207c5b53213d', 'Ignacio', 'Norambuena', '21.013.703-3', 'ignacio.norambuena1990@gmail.com', 'Banco Familia', 'Cuenta Corriente', '0001234572', 0);

console.log('✅ Base de datos demo-bank inicializada en:', dbPath);

export interface DemoUser {
  id: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  rut: string;
  balance: number;
  account_number: string;
  transfer_pin: string;
  biometric_user_id: string | null;
  enrollment_id: string | null;
  is_voice_enrolled: number; // 0 = false, 1 = true
  created_at: string;
  updated_at: string;
}

export interface Contact {
  id: number;
  user_id: string;
  first_name: string;
  last_name: string;
  rut: string;
  email: string;
  bank_name: string;
  account_type: string;
  account_number: string;
  is_favorite: number;
  created_at: string;
}

export interface Transaction {
  id: number;
  user_id: string;
  type: string;
  amount: number;
  recipient_first_name: string | null;
  recipient_last_name: string | null;
  recipient_rut: string | null;
  recipient_email: string | null;
  recipient_bank: string | null;
  recipient_account_type: string | null;
  recipient_account_number: string | null;
  description: string | null;
  status: string;
  verification_method: string | null;
  verification_id: string | null;
  created_at: string;
}

export interface Session {
  token: string;
  user_id: string;
  created_at: string;
  expires_at: string;
}

// Funciones para usuarios
export const userQueries = {
  getByEmail: db.prepare<[string]>('SELECT * FROM users WHERE email = ?'),
  getById: db.prepare<[string]>('SELECT * FROM users WHERE id = ?'),
  getByBiometricId: db.prepare<[string]>('SELECT * FROM users WHERE biometric_user_id = ?'),
  updateBalance: db.prepare<[number, string]>('UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
  updateBiometricId: db.prepare<[string, string, string]>('UPDATE users SET biometric_user_id = ?, enrollment_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
  updateEnrollmentStatus: db.prepare<[number, string]>('UPDATE users SET is_voice_enrolled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
  clearEnrollmentId: db.prepare<[string]>('UPDATE users SET enrollment_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
  updatePin: db.prepare<[string, string]>('UPDATE users SET transfer_pin = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
};

// Funciones para contactos
export const contactQueries = {
  getByUser: db.prepare<[string]>('SELECT * FROM contacts WHERE user_id = ? ORDER BY is_favorite DESC, first_name ASC'),
  getById: db.prepare<[number]>('SELECT * FROM contacts WHERE id = ?'),
  create: db.prepare<[string, string, string, string, string, string, string, string, number]>(`
    INSERT INTO contacts (user_id, first_name, last_name, rut, email, bank_name, account_type, account_number, is_favorite)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `),
  delete: db.prepare<[number]>('DELETE FROM contacts WHERE id = ?'),
  toggleFavorite: db.prepare<[number, number]>('UPDATE contacts SET is_favorite = ? WHERE id = ?'),
};

// Funciones para transacciones
export const transactionQueries = {
  create: db.prepare<[string, string, number, string | null, string | null, string | null, string | null, string | null, string | null, string | null, string, string | null, string | null]>(`
    INSERT INTO transactions (user_id, type, amount, recipient_first_name, recipient_last_name, recipient_rut, recipient_email, recipient_bank, recipient_account_type, recipient_account_number, description, status, verification_method, verification_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `),
  getByUser: db.prepare<[string]>('SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50'),
  updateStatus: db.prepare<[string, number]>('UPDATE transactions SET status = ? WHERE id = ?'),
};

// Funciones para sesiones
export const sessionQueries = {
  create: db.prepare<[string, string, string]>('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)'),
  getByToken: db.prepare<[string]>('SELECT * FROM sessions WHERE token = ?'),
  delete: db.prepare<[string]>('DELETE FROM sessions WHERE token = ?'),
  deleteExpired: db.prepare('DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP'),
};

// Limpiar sesiones expiradas cada hora
setInterval(() => {
  sessionQueries.deleteExpired.run();
}, 60 * 60 * 1000);

export default db;
