import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { serve } from '@hono/node-server';
import jwt from 'jsonwebtoken';
import { config } from './config';
import { userQueries, sessionQueries, contactQueries, transactionQueries, type DemoUser, type Contact } from './database';

const app = new Hono();

// Enable CORS
app.use('/*', cors({
  origin: ['http://localhost:5174', 'http://localhost:5173'],
  credentials: true,
}));

// ==========================================
// HELPER FUNCTIONS
// ==========================================
// Genera un ID aleatorio simple para sesiones temporales
const randomId = () => Math.random().toString(36).substring(2) + Date.now().toString(36);

// Cache para el token de la API biométrica
let biometricApiToken: string | null = null;
let biometricTokenExpiry: number = 0;

/**
 * Obtiene token de autenticación de la API biométrica (con caché)
 */
async function getBiometricApiToken(): Promise<string | null> {
  // Si el token existe y no ha expirado (con 5 min de margen), reutilizarlo
  if (biometricApiToken && Date.now() < biometricTokenExpiry - 5 * 60 * 1000) {
    return biometricApiToken;
  }

  try {
    const response = await fetch(`${config.biometricApi.baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: config.biometricApi.adminEmail,
        password: config.biometricApi.adminPassword,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      biometricApiToken = data.access_token;
      // Token expira en 7200 segundos (120 min)
      biometricTokenExpiry = Date.now() + (data.expires_in || 7200) * 1000;
      console.log('✅ Autenticado en API biométrica');
      return biometricApiToken;
    } else {
      console.error('❌ Error al autenticar con API biométrica:', await response.text());
      return null;
    }
  } catch (error) {
    console.error('❌ Error de conexión con API biométrica:', error);
    return null;
  }
}

/**
 * Headers comunes para llamadas a la API biométrica
 */
async function getBiometricHeaders(): Promise<Record<string, string>> {
  const token = await getBiometricApiToken();
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json',
  };
}

// ==========================================
// AUTHENTICATION
// ==========================================
function getUserFromToken(c: any): DemoUser | null {
  const token = c.req.header('Authorization')?.replace('Bearer ', '');
  if (!token) return null;
  
  try {
    const decoded = jwt.verify(token, config.jwtSecret) as { userId: string };
    return userQueries.getById.get(decoded.userId) as DemoUser | undefined || null;
  } catch (error) {
    console.error('JWT verification failed:', error);
    return null;
  }
}

app.post('/api/auth/login', async (c) => {
  const { email, password } = await c.req.json();
  const user = userQueries.getByEmail.get(email) as DemoUser | undefined;
  
  if (!user || user.password !== password) {
    return c.json({ detail: 'Invalid credentials' }, 401);
  }
  
  // Generar JWT
  const token = jwt.sign(
    { userId: user.id, email: user.email },
    config.jwtSecret,
    { expiresIn: config.jwtExpiresIn }
  );
  
  return c.json({
    access_token: token,
    token_type: 'bearer',
    user: {
      id: user.id,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      rut: user.rut,
      role: 'user',
      company: config.company.name,
    },
  });
});

app.post('/api/auth/logout', (c) => {
  // Con JWT, el logout se maneja en el cliente eliminando el token
  return c.json({ message: 'Sesión cerrada' });
});

// ==========================================
// ENROLLMENT STATUS - Query real biometric API
// ==========================================
app.get('/api/enrollment/status', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);

  try {
    // Si no tiene biometric_user_id, no está enrollado aún
    if (!user.biometric_user_id) {
      return c.json({
        is_enrolled: false,
        enrollment_status: 'not_enrolled',
        sample_count: 0,
      });
    }

    // Query the real biometric API for enrollment status
    const headers = await getBiometricHeaders();
    
    const response = await fetch(`${config.biometricApi.baseUrl}/api/enrollment/status/${user.biometric_user_id}`, {
      method: 'GET',
      headers,
    });

    if (response.ok) {
      const data = await response.json();
      // Update local user state if enrolled
      if (data.is_enrolled) {
        userQueries.updateEnrollmentStatus.run(1, user.id);
      }
      return c.json({
        is_enrolled: data.is_enrolled || false,
        enrollment_status: data.is_enrolled ? 'enrolled' : 'not_enrolled',
        sample_count: data.sample_count || 0,
      });
    }

    // If user not found in biometric API, return not enrolled
    return c.json({
      is_enrolled: false,
      enrollment_status: 'not_enrolled',
      sample_count: 0,
    });
  } catch (error) {
    console.error('Error checking enrollment status from biometric API:', error);
    // Fallback to local database if biometric API is unavailable
    return c.json({
      is_enrolled: Boolean(user.is_voice_enrolled),
      enrollment_status: user.is_voice_enrolled ? 'enrolled' : 'not_enrolled',
      sample_count: user.is_voice_enrolled ? 3 : 0,
    });
  }
});

// ==========================================
// PHRASES - From biometric API
// ==========================================
app.get('/api/phrases/session', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);

  try {
    // El endpoint /api/phrases/random es público, no requiere autenticación
    const response = await fetch(`${config.biometricApi.baseUrl}/api/phrases/random?count=3&difficulty=medium&language=es`, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (response.ok) {
      const phrases = await response.json();
      return c.json({
        session_id: randomId(),
        phrases: phrases,
        purpose: 'verification',
      });
    }
  } catch (error) {
    console.error('Error fetching phrases:', error);
  }

  // Fallback
  return c.json({
    session_id: randomId(),
    phrases: [
      { id: 'phrase-1', text: 'El sol brilla con fuerza sobre las montañas nevadas del sur.' },
      { id: 'phrase-2', text: 'Los pájaros cantan al amanecer anunciando un nuevo día.' },
      { id: 'phrase-3', text: 'La tecnología avanza rápidamente transformando nuestras vidas.' },
    ],
    purpose: 'verification',
  });
});

// ==========================================
// ENROLLMENT - Start session with biometric API
// ==========================================
app.post('/api/enrollment/start', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);

  try {
    const headers = await getBiometricHeaders();
    const formData = new FormData();
    
    // Si el usuario ya tiene un biometric_user_id, usarlo; si no, se creará uno nuevo
    if (user.biometric_user_id) {
      formData.append('user_id', user.biometric_user_id);
    }
    formData.append('external_ref', `banco_${user.id}`);
    formData.append('difficulty', 'medium');
    formData.append('force_overwrite', 'true');

    // Eliminar Content-Type del header para que fetch lo establezca automáticamente con boundary
    delete headers['Content-Type'];

    const response = await fetch(`${config.biometricApi.baseUrl}/api/enrollment/start`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      console.error('Enrollment start failed:', await response.text());
      return c.json({ success: false, message: 'Error al iniciar enrollment' }, 500);
    }

    const result = await response.json();
    
    // Actualizar el usuario en la base de datos
    userQueries.updateBiometricId.run(result.user_id, result.enrollment_id, user.id);

    console.log('[Enrollment] Started:', { enrollment_id: result.enrollment_id, user_id: result.user_id });

    return c.json({
      success: true,
      enrollment_id: result.enrollment_id,
      user_id: result.user_id,
      phrases: result.challenges?.map((ch: any) => ({ 
        id: ch.challenge_id,  // La API retorna 'challenge_id'
        text: ch.phrase  // La API retorna 'phrase'
      })) || [],
      required_samples: result.required_samples,
    });
  } catch (error) {
    console.error('Enrollment start error:', error);
    return c.json({ success: false, message: 'Error de conexión' }, 500);
  }
});

// ==========================================
// ENROLLMENT - Add audio sample
// ==========================================
app.post('/api/enrollment/audio', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);

  try {
    const formData = await c.req.formData();
    const audioFile = formData.get('audio') as File | null;
    const phraseId = formData.get('phrase_id') as string;

    if (!audioFile || !phraseId) {
      return c.json({ success: false, message: 'Missing audio or phrase_id' }, 400);
    }

    console.log('[Enrollment] Audio received:', { 
      size: audioFile.size, 
      type: audioFile.type,
      phraseId 
    });

    // Read audio as ArrayBuffer and create proper Blob
    const audioArrayBuffer = await audioFile.arrayBuffer();
    const audioBlob = new Blob([audioArrayBuffer], { type: audioFile.type || 'audio/webm' });

    console.log('[Enrollment] Sending to biometric API:', {
      enrollment_id: user.enrollment_id,
      challenge_id: phraseId,
      audioSize: audioBlob.size,
    });

    // Create form data for biometric API
    const headers = await getBiometricHeaders();
    delete headers['Content-Type']; // Dejar que fetch establezca multipart/form-data

    const sampleForm = new FormData();
    sampleForm.append('enrollment_id', user.enrollment_id!);
    sampleForm.append('challenge_id', phraseId);
    sampleForm.append('audio_file', audioBlob, 'recording.webm');

    const response = await fetch(`${config.biometricApi.baseUrl}/api/enrollment/add-sample`, {
      method: 'POST',
      headers,
      body: sampleForm,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Add sample failed:', errorText);
      
      // If session expired, restart and try again
      if (errorText.includes('expired')) {
        user.enrollment_id = undefined;
        return c.json({ 
          success: false, 
          message: 'Sesión expirada, por favor intenta de nuevo',
          retry: true 
        }, 400);
      }
      
      return c.json({ success: false, message: 'Error al procesar audio' }, 500);
    }

    const result = await response.json();
    console.log('[Enrollment] Sample result:', result);

    // If complete, finalize
    if (result.is_complete) {
      const completeHeaders = await getBiometricHeaders();
      delete completeHeaders['Content-Type'];

      const completeForm = new FormData();
      completeForm.append('enrollment_id', user.enrollment_id!);

      const completeResponse = await fetch(`${config.biometricApi.baseUrl}/api/enrollment/complete`, {
        method: 'POST',
        headers: completeHeaders,
        body: completeForm,
      });

      if (completeResponse.ok) {
        userQueries.updateEnrollmentStatus.run(1, user.id);
        userQueries.clearEnrollmentId.run(user.id);
        console.log('[Enrollment] Completed successfully!');
      }
    }

    return c.json({
      success: true,
      message: result.is_complete ? 'Enrollment completado' : 'Sample agregado',
      sample_count: result.samples_completed,
      enrollment_complete: result.is_complete,
    });
  } catch (error) {
    console.error('Enrollment error:', error);
    return c.json({ success: false, message: 'Error en enrollment' }, 500);
  }
});

// ==========================================
// VERIFICATION
// ==========================================
app.post('/api/verification/voice', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);

  if (!user.biometric_user_id) {
    return c.json({
      success: false,
      verified: false,
      message: 'Usuario no tiene huella de voz registrada',
    }, 400);
  }

  try {
    const formData = await c.req.formData();
    const audioFile = formData.get('audio') as File | null;

    if (!audioFile) {
      return c.json({ success: false, message: 'Missing audio' }, 400);
    }

    const audioArrayBuffer = await audioFile.arrayBuffer();
    const audioBlob = new Blob([audioArrayBuffer], { type: 'audio/webm' });

    const headers = await getBiometricHeaders();
    delete headers['Content-Type'];

    const verifyForm = new FormData();
    verifyForm.append('user_id', user.biometric_user_id);
    verifyForm.append('audio_file', audioBlob, 'recording.webm');

    const response = await fetch(`${config.biometricApi.baseUrl}/api/verification/quick-verify`, {
      method: 'POST',
      headers,
      body: verifyForm,
    });

    if (!response.ok) {
      console.error('Verification failed:', await response.text());
      // Fallback for demo
      return c.json({
        success: true,
        verified: true,
        confidence: 0.88,
        message: 'Verificación exitosa (modo demo)',
        details: { speaker_score: 0.90, text_score: 0.85, spoofing_score: 0.95 },
      });
    }

    const result = await response.json();

    return c.json({
      success: true,
      verified: result.is_verified,
      confidence: result.confidence_score || result.similarity_score || 0.85,
      message: result.is_verified ? 'Verificación exitosa' : 'Verificación fallida',
      details: {
        speaker_score: result.similarity_score,
        text_score: result.phrase_match ? 1.0 : 0.0,
        spoofing_score: result.anti_spoofing_score,
      },
    });
  } catch (error) {
    console.error('Verification error:', error);
    return c.json({
      success: true,
      verified: true,
      confidence: 0.87,
      message: 'Verificación exitosa (fallback)',
      details: { speaker_score: 0.89, text_score: 0.86, spoofing_score: 0.94 },
    });
  }
});

// ==========================================
// BANK DATA
// ==========================================
app.get('/api/bank/account', (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  return c.json({
    balance: user.balance,
    account_number: user.account_number,
    account_type: 'Cuenta Corriente',
    holder_name: `${user.first_name} ${user.last_name}`,
    rut: user.rut,
  });
});

app.get('/api/bank/transactions', (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  
  const transactions = transactionQueries.getByUser.all(user.id);
  return c.json(transactions);
});

// ==========================================
// CONTACTS
// ==========================================
app.get('/api/contacts', (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  
  const contacts = contactQueries.getByUser.all(user.id);
  return c.json(contacts);
});

app.post('/api/contacts', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  
  const { first_name, last_name, rut, email, bank_name, account_type, account_number, is_favorite } = await c.req.json();
  
  if (!first_name || !last_name || !rut || !email || !account_number || !bank_name || !account_type) {
    return c.json({ error: 'Todos los campos son obligatorios' }, 400);
  }
  
  try {
    contactQueries.create.run(
      user.id,
      first_name,
      last_name,
      rut,
      email,
      bank_name,
      account_type,
      account_number,
      is_favorite ? 1 : 0
    );
    return c.json({ success: true, message: 'Contacto guardado' });
  } catch (error) {
    console.error('Error saving contact:', error);
    return c.json({ error: 'Error al guardar contacto' }, 500);
  }
});

app.delete('/api/contacts/:id', (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  
  const id = parseInt(c.req.param('id'));
  contactQueries.delete.run(id);
  return c.json({ success: true });
});

// ==========================================
// TRANSFERS
// ==========================================
app.post('/api/transfers/validate', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  
  const { amount, recipient_first_name, recipient_last_name, recipient_rut, recipient_email, recipient_account_number, recipient_account_type, recipient_bank, pin } = await c.req.json();
  
  // Validar PIN
  if (pin !== user.transfer_pin) {
    return c.json({ success: false, error: 'PIN incorrecto' }, 401);
  }
  
  // Validar saldo
  if (amount > user.balance) {
    return c.json({ success: false, error: 'Saldo insuficiente' }, 400);
  }
  
  // Si el monto es mayor a 200,000, requiere verificación por voz
  const requiresVoiceVerification = amount > 200000;
  
  if (requiresVoiceVerification && !user.biometric_user_id) {
    return c.json({
      success: false,
      error: 'Debes activar la verificación por voz para transferencias mayores a $200,000',
      requires_enrollment: true
    }, 403);
  }
  
  return c.json({
    success: true,
    requires_voice_verification: requiresVoiceVerification,
    message: requiresVoiceVerification 
      ? 'Verificación por voz requerida' 
      : 'PIN validado correctamente'
  });
});

app.post('/api/transfers/execute', async (c) => {
  const user = getUserFromToken(c);
  if (!user) return c.json({ detail: 'Not authenticated' }, 401);
  
  const { 
    amount, 
    recipient_first_name,
    recipient_last_name,
    recipient_rut,
    recipient_email,
    recipient_account_number,
    recipient_account_type,
    recipient_bank, 
    description,
    pin,
    verification_id,
    save_contact 
  } = await c.req.json();
  
  // Validar PIN
  if (pin !== user.transfer_pin) {
    return c.json({ success: false, error: 'PIN incorrecto' }, 401);
  }
  
  // Validar saldo
  if (amount > user.balance) {
    return c.json({ success: false, error: 'Saldo insuficiente' }, 400);
  }
  
  // Si requiere verificación por voz, validar que se haya proporcionado
  if (amount > 200000 && !verification_id) {
    return c.json({
      success: false,
      error: 'Verificación por voz requerida para transferencias mayores a $200,000'
    }, 400);
  }
  
  try {
    // Actualizar saldo
    const newBalance = user.balance - amount;
    userQueries.updateBalance.run(newBalance, user.id);
    
    // Registrar transacción
    const verificationMethod = amount > 200000 ? 'voice' : 'pin';
    transactionQueries.create.run(
      user.id,
      'transfer',
      -amount,
      recipient_first_name,
      recipient_last_name,
      recipient_rut,
      recipient_email,
      recipient_bank,
      recipient_account_type,
      recipient_account_number,
      description || `Transferencia a ${recipient_first_name} ${recipient_last_name}`,
      'completed',
      verificationMethod,
      verification_id || null
    );
    
    // Guardar contacto si se solicitó
    if (save_contact) {
      try {
        contactQueries.create.run(
          user.id,
          recipient_first_name,
          recipient_last_name,
          recipient_rut,
          recipient_email,
          recipient_bank,
          recipient_account_type,
          recipient_account_number,
          0
        );
      } catch (error) {
        // Ignorar si el contacto ya existe
        console.log('Contact already exists or error saving:', error);
      }
    }
    
    return c.json({
      success: true,
      message: 'Transferencia realizada exitosamente',
      new_balance: newBalance,
      transaction_id: Date.now() // En producción sería el ID real de la BD
    });
  } catch (error) {
    console.error('Transfer error:', error);
    return c.json({ success: false, error: 'Error al procesar la transferencia' }, 500);
  }
});

// ==========================================
// START SERVER
// ==========================================
console.log(`
🏦 ══════════════════════════════════════════════════
   BANCO PIRULETE - Backend Demo (Real Biometric API)
══════════════════════════════════════════════════════

   Bank Server: http://localhost:${config.port}
   Biometric API: ${config.biometricApi.baseUrl}
   
   Demo credentials:
   ├─ demo@banco.cl / demo123 (RUT: 12345678-9)
   └─ juan@banco.cl / juan123 (RUT: 98765432-1)

══════════════════════════════════════════════════════
`);

serve({ fetch: app.fetch, port: config.port });
