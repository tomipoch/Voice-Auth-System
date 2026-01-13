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
    transfer_pin TEXT DEFAULT '123456',
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
    email TEXT NOT NULL,
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

// Insertar usuarios demo si no existen
const seedUsers = db.prepare(`
  INSERT OR IGNORE INTO users (
    id, email, password, first_name, last_name, rut, 
    balance, account_number, transfer_pin, biometric_user_id, is_voice_enrolled
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

// Usuario 1 - demo@banco.cl (enrollado)
seedUsers.run(
  'demo-user-1',
  'demo@banco.cl',
  'demo123',
  'Tomás',
  'P.',
  '12345678-9',
  1850420,
  '1234567890',
  '123456', // PIN de transferencias
  '85504b66-b04f-48a7-a513-3af8c55f9cfb', // ID real de la API
  0 // Inicialmente no enrollado
);

// Usuario 2 - juan@banco.cl (enrollado en la API)
seedUsers.run(
  'demo-user-2',
  'juan@banco.cl',
  'juan123',
  'Juan',
  'Pérez',
  '98765432-1',
  850000,
  '0987654321',
  '654321', // PIN de transferencias
  'a593fd09-8c2e-49a4-8823-38e77ef5fe0b', // ID real de la API
  1 // Ya está enrollado en la API
);

// Insertar contactos demo
const seedContacts = db.prepare(`
  INSERT OR IGNORE INTO contacts (
    user_id, first_name, last_name, rut, email, bank_name, account_type, account_number, is_favorite
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

// Contactos para demo@banco.cl
seedContacts.run('demo-user-1', 'María', 'González', '12.345.678-9', 'maria.gonzalez@example.com', 'Banco Estado', 'Cuenta Corriente', '9876543210', 1);
seedContacts.run('demo-user-1', 'Pedro', 'Rodríguez', '98.765.432-1', 'pedro.rodriguez@example.com', 'Banco Chile', 'Cuenta Vista', '1122334455', 0);
seedContacts.run('demo-user-1', 'Ana', 'Martínez', '11.223.344-5', 'ana.martinez@example.com', 'Banco Santander', 'Cuenta de Ahorro', '5544332211', 0);

// Contactos para juan@banco.cl
seedContacts.run('demo-user-2', 'Carlos', 'Silva', '55.667.788-9', 'carlos.silva@example.com', 'Banco Falabella', 'Cuenta Corriente', '6677889900', 1);

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
