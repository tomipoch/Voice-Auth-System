#!/usr/bin/env node

/**
 * Script para verificar configuración de ambiente
 * Valida que todas las variables necesarias estén definidas
 */

const fs = require('fs');
const path = require('path');

// Colores para consola
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

// Función para logs con color
const log = (message, color = 'reset') => {
  console.log(`${colors[color]}${message}${colors.reset}`);
};

// Variables requeridas por ambiente
const requiredVars = {
  development: [
    'VITE_APP_NAME',
    'VITE_API_BASE_URL',
    'VITE_DEBUG',
    'VITE_ENABLE_MOCK_DATA'
  ],
  production: [
    'VITE_APP_NAME',
    'VITE_API_BASE_URL',
    'VITE_DEBUG',
    'VITE_ENABLE_ANALYTICS'
  ],
  staging: [
    'VITE_APP_NAME',
    'VITE_API_BASE_URL',
    'VITE_DEBUG'
  ]
};

// Función para cargar archivo .env
function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const env = {};
  
  content.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key) {
        env[key.trim()] = valueParts.join('=').trim();
      }
    }
  });

  return env;
}

// Función principal
function checkEnvironment() {
  const environment = process.argv[2] || 'development';
  
  log('\n🔧 VoiceAuth Environment Checker', 'bright');
  log('═'.repeat(50), 'cyan');
  
  log(`\n📋 Checking environment: ${environment}`, 'blue');
  
  // Archivos de configuración
  const envFiles = [
    '.env',
    `.env.${environment}`,
    '.env.local'
  ];
  
  let allVars = {};
  let filesFound = 0;
  
  // Cargar variables de todos los archivos
  envFiles.forEach(file => {
    const filePath = path.join(__dirname, '..', file);
    const vars = loadEnvFile(filePath);
    
    if (Object.keys(vars).length > 0) {
      allVars = { ...allVars, ...vars };
      filesFound++;
      log(`✅ Found: ${file} (${Object.keys(vars).length} vars)`, 'green');
    } else if (fs.existsSync(filePath)) {
      log(`⚠️  Empty: ${file}`, 'yellow');
    } else {
      log(`❌ Missing: ${file}`, 'red');
    }
  });
  
  if (filesFound === 0) {
    log('\n❌ No environment files found!', 'red');
    process.exit(1);
  }
  
  // Verificar variables requeridas
  log(`\n📝 Checking required variables for ${environment}:`, 'blue');
  
  const required = requiredVars[environment] || requiredVars.development;
  let missing = 0;
  let warnings = 0;
  
  required.forEach(varName => {
    if (allVars[varName]) {
      const value = allVars[varName];
      if (value.includes('localhost') && environment === 'production') {
        log(`⚠️  ${varName}: ${value} (localhost in production!)`, 'yellow');
        warnings++;
      } else {
        log(`✅ ${varName}: ${value}`, 'green');
      }
    } else {
      log(`❌ ${varName}: Missing`, 'red');
      missing++;
    }
  });
  
  // Verificaciones adicionales
  log('\n🔍 Additional checks:', 'blue');
  
  // Verificar URLs
  const apiUrl = allVars.VITE_API_BASE_URL;
  if (apiUrl) {
    try {
      new URL(apiUrl);
      log(`✅ API URL format: Valid`, 'green');
    } catch {
      log(`❌ API URL format: Invalid`, 'red');
      missing++;
    }
  }
  
  // Verificar configuración de debug
  const debug = allVars.VITE_DEBUG;
  if (environment === 'production' && debug === 'true') {
    log(`⚠️  Debug enabled in production`, 'yellow');
    warnings++;
  }
  
  // Verificar mock data
  const mockData = allVars.VITE_ENABLE_MOCK_DATA;
  if (environment === 'production' && mockData === 'true') {
    log(`⚠️  Mock data enabled in production`, 'yellow');
    warnings++;
  }
  
  // Resultados
  log('\n📊 Summary:', 'bright');
  log(`Environment: ${environment}`, 'blue');
  log(`Files loaded: ${filesFound}`, 'blue');
  log(`Total variables: ${Object.keys(allVars).length}`, 'blue');
  log(`Missing required: ${missing}`, missing > 0 ? 'red' : 'green');
  log(`Warnings: ${warnings}`, warnings > 0 ? 'yellow' : 'green');
  
  if (missing > 0) {
    log('\n❌ Environment check failed!', 'red');
    log('Please fix missing variables and try again.', 'red');
    process.exit(1);
  } else if (warnings > 0) {
    log('\n⚠️  Environment check passed with warnings.', 'yellow');
  } else {
    log('\n✅ Environment check passed!', 'green');
  }
  
  log('═'.repeat(50), 'cyan');
}

// Ejecutar si es llamado directamente
if (require.main === module) {
  checkEnvironment();
}

module.exports = { checkEnvironment, loadEnvFile };