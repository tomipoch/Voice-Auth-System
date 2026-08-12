# Manual de Usuario
## Sistema de Autenticación por Biometría de Voz

**Versión**: 1.0.0  
**Fecha**: Diciembre 2024

---

## 📋 Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Guía de Inicio Rápido](#2-guía-de-inicio-rápido)
3. [Para Usuarios](#3-para-usuarios)
4. [Para Administradores](#4-para-administradores)
5. [Solución de Problemas](#5-solución-de-problemas)
6. [Preguntas Frecuentes](#6-preguntas-frecuentes)
7. [Seguridad y Privacidad](#7-seguridad-y-privacidad)

---

## 1. Introducción

### ¿Qué es este sistema?

Este sistema permite autenticar usuarios mediante el reconocimiento de su voz, ofreciendo una forma segura y conveniente de verificar identidad sin necesidad de contraseñas adicionales o dispositivos físicos.

### Características Principales

✅ **Autenticación por voz** - Verifica tu identidad hablando  
✅ **Seguro** - Tecnología de ML con detección anti-suplantación  
✅ **Rápido** - Verificación en segundos  
✅ **Conveniente** - No requiere hardware especial  
✅ **Multi-usuario** - Gestión de múltiples usuarios por empresa

### Requisitos del Sistema

**Hardware**:
- Micrófono funcional (integrado o externo)
- Conexión a internet estable

**Software**:
- Navegador web moderno:
  - Chrome 90+ (recomendado)
  - Firefox 88+
  - Safari 14+
  - Edge 90+
- Permisos de micrófono habilitados

---

## 2. Guía de Inicio Rápido

### 2.1 Acceso al Sistema

1. **Abrir el navegador** y navegar a la URL del sistema
2. Verás la pantalla de inicio de sesión

### 2.2 Crear una Cuenta Nueva

**Si es la primera vez que usas el sistema:**

1. Click en **"Crear cuenta"** o **"Registrarse"**
2. Completa el formulario de registro:
   - **Nombre**: Tu nombre completo
   - **Apellido**: Tu apellido
   - **Email**: Tu correo electrónico (será tu usuario)
   - **Contraseña**: Mínimo 8 caracteres, debe incluir:
     - Al menos 1 mayúscula
     - Al menos 1 minúscula
     - Al menos 1 número
   - **Empresa** (opcional): Nombre de tu organización
3. Click en **"Registrarse"**
4. Si todo está correcto, verás un mensaje de confirmación

> **💡 Tip**: Usa una contraseña segura y única. Ej: `MiVoz2024!`

### 2.3 Iniciar Sesión

1. Ingresa tu **email** y **contraseña**
2. Click en **"Iniciar Sesión"**
3. Serás dirigido al dashboard principal

---

## 3. Para Usuarios

### 3.1 Dashboard Principal

Después de iniciar sesión verás:

- **📊 Panel superior**: Información de tu cuenta
- **🎤 Estado de enrollment**: Si tu voz está registrada
- **✅ Estado de verificación**: Tu última verificación
- **⚙️ Configuración**: Acceso a tu perfil

### 3.2 Configuración de Perfil

**Para acceder a tu perfil:**

1. Click en tu nombre o avatar (esquina superior derecha)
2. Selecciona **"Perfil"** o **"Mi Cuenta"**

**Información que puedes actualizar:**
- Nombre y apellido
- RUT (opcional)
- Configuraciones de preferencias

**Para cambiar tu contraseña:**

1. Ve a **Perfil** → **Cambiar Contraseña**
2. Ingresa:
   - Contraseña actual
   - Nueva contraseña (debe cumplir requisitos)
   - Confirmar nueva contraseña
3. Click en **"Actualizar Contraseña"**

### 3.3 Proceso de Enrollment (Registro de Voz)

**¿Qué es el enrollment?**  
Es el proceso de registrar tu voz en el sistema para crear tu perfil biométrico único.

**Pasos para registrar tu voz:**

1. **Ir a Enrollment**:
   - Desde el dashboard, click en **"Registrar Voz"** o **"Enrollment"**

2. **Preparación**:
   - Asegúrate de estar en un lugar tranquilo
   - Verifica que tu micrófono esté conectado
   - El sistema te pedirá permiso para usar el micrófono → **"Permitir"**

3. **Grabación de muestras**:
   - El sistema mostrará **3-5 frases** diferentes
   - Para cada frase:
     - Lee la frase en voz alta claramente
     - Click en el botón de **🎤 Grabar**
     - Lee la frase mientras se graba (3-5 segundos)
     - Click en **⏹️ Detener** cuando termines
   - El sistema validará la calidad del audio

4. **Completar enrollment**:
   - Una vez grabadas todas las frases correctamente
   - Click en **"Completar Enrollment"**
   - Verás mensaje de confirmación: ✅ **"Voz registrada exitosamente"**

> **⚠️ Importante**:
> - Habla con tu tono de voz natural
> - Lee claramente y sin apuros
> - Evita ruido de fondo
> - Si una grabación no es aceptada, simplemente vuelve a intentar

**Ejemplo de frases que podrías leer:**
- "La voz es única como una huella digital"
- "El cielo está despejado esta mañana"
- "La tecnología avanza cada día más"

### 3.4 Verificación de Identidad por Voz

**¿Cuándo usar la verificación?**  
Cuando necesites confirmar tu identidad para acceder a funciones seguras o recursos protegidos.

**Pasos para verificarte:**

1. **Iniciar verificación**:
   - Click en **"Verificar Identidad"** o **"Verificación de Voz"**

2. **Leer la frase**:
   - El sistema mostrará una frase aleatoria
   - Click en **🎤 Grabar**
   - Lee la frase claramente
   - Click en **⏹️ Detener**

3. **Resultado**:
   - ✅ **Verificación exitosa**: "Identidad confirmada"
   - ❌ **Verificación fallida**: "No se pudo verificar, intenta nuevamente"

**Tipos de verificación:**

- **Verificación Simple**: Una sola frase
- **Verificación Multi-Frase**: 2-3 frases para mayor seguridad

> **💡 Consejo**: Si fallas la verificación, asegúrate de:
> - Estar en un lugar sin ruido
> - Hablar con tu tono natural
> - Leer toda la frase completa

### 3.5 Historial de Verificaciones

**Para ver tu historial:**

1. Ve a **Perfil** → **Historial** o desde el Dashboard
2. Verás una lista con:
   - 📅 Fecha y hora de cada verificación
   - ✅/❌ Resultado (exitosa o fallida)
   - 📊 Puntuación de confianza

---

## 4. Para Administradores

### 4.1 Acceso al Panel de Administración

**Requisitos**: Necesitas rol de **Administrador** o **Superadministrador**

**Para acceder:**
1. Inicia sesión con tu cuenta de administrador
2. En el menú lateral verás **"Administración"** o **"Admin Panel"**
3. Click para acceder

### 4.2 Gestión de Usuarios

**Ver lista de usuarios:**

1. Ve a **Admin** → **Usuarios**
2. Verás una tabla con todos los usuarios de tu empresa:
   - Nombre y email
   - Estado (activo/inactivo)
   - Estado de enrollment
   - Fecha de registro

**Buscar usuarios:**
- Usa la barra de búsqueda superior
- Busca por email o nombre

**Acciones sobre usuarios:**

**Ver detalles de un usuario:**
1. Click en el nombre del usuario
2. Verás:
   - Información completa del perfil
   - Estado biométrico (si tiene voz registrada)
   - Historial de verificaciones
   - Métricas de uso

**Activar/Desactivar usuario:**
1. Desde la lista de usuarios
2. Click en el botón de estado (🟢 Activo / 🔴 Inactivo)
3. Confirma la acción
4. El usuario no podrá acceder si está inactivo

**Eliminar usuario:**
1. Ve a los detalles del usuario
2. Click en **"Eliminar Usuario"** (botón rojo)
3. **⚠️ Confirma** - Esta acción NO se puede deshacer
4. Se eliminarán:
   - Perfil del usuario
   - Datos biométricos
   - Historial de verificaciones

> **⚠️ Precaución**: Solo elimina usuarios cuando sea absolutamente necesario. La acción es irreversible.

### 4.3 Estadísticas del Sistema

**Ver estadísticas generales:**

1. Ve a **Admin** → **Dashboard** o **Estadísticas**
2. Verás:
   - 👥 **Total de usuarios** registrados
   - 🎤 **Usuarios con enrollment** completado
   - ✅ **Tasa de éxito** de verificaciones
   - 📊 **Actividad reciente**

**Métricas disponibles:**
- Usuarios registrados hoy/semana/mes
- Verificaciones exitosas vs fallidas
- Usuarios más activos
- Tendencias de uso

### 4.4 Gestión de Frases

**¿Qué son las frases?**  
Las frases que los usuarios leen durante enrollment y verificación.

**Ver frases disponibles:**

1. Ve a **Admin** → **Frases**
2. Verás la lista completa de frases
3. Puedes filtrar por:
   - **Libro**: Fuente de la frase
   - **Autor**: Autor del texto
   - **Estado**: Activa/Inactiva

**Acciones sobre frases:**

**Activar/Desactivar frase:**
- Click en el toggle de estado
- Frases inactivas no se usan en el sistema

**Eliminar frase:**
- Click en el botón de eliminar (🗑️)
- Confirma la acción

**Estadísticas de frases:**
- Total de frases activas
- Distribución por libro/autor
- Frases más usadas

### 4.5 Configuración del Sistema

**Reglas de calidad de frases:**

1. Ve a **Admin** → **Configuración** → **Reglas de Frases**
2. Ajusta parámetros como:
   - Longitud mínima de frases
   - Caracteres especiales permitidos
   - Idioma

**Logs de auditoría:**

1. Ve a **Admin** → **Logs** o **Auditoría**
2. Verás registro de:
   - Logins y logouts
   - Cambios en usuarios
   - Acciones administrativas
3. Útil para rastrear actividad y seguridad

---

## 5. Solución de Problemas

### 5.1 Problemas Comunes

#### ❌ "No se detecta el micrófono"

**Solución:**
1. Verifica que el micrófono esté conectado
2. En el navegador:
   - Click en el icono de candado (🔒) en la barra de dirección
   - Asegúrate que **"Micrófono"** esté en **"Permitir"**
3. En Windows:
   - Configuración → Privacidad → Micrófono → Activar
4. En Mac:
   - Preferencias del Sistema → Seguridad y Privacidad → Micrófono → Marcar tu navegador

#### ❌ "Calidad de audio insuficiente"

**Solución:**
1. Acércate más al micrófono
2. Reduce el ruido de fondo
3. Habla más fuerte y claro
4. Prueba con auriculares con micrófono integrado

#### ❌ "Verificación fallida repetidamente"

**Solución:**
1. Asegúrate de leer la frase completa
2. Usa el mismo tono de voz que en el enrollment
3. Evita murmurar o gritar
4. Si persiste, considera hacer un nuevo enrollment

#### ❌ "Error al iniciar sesión"

**Solución:**
1. Verifica email y contraseña
2. Recuerda que la contraseña es **sensible a mayúsculas/minúsculas**
3. Si olvidaste tu contraseña:
   - Click en "Olvidé mi contraseña"
   - Contacta al administrador

#### ❌ "La página no carga"

**Solución:**
1. Verifica tu conexión a internet
2. Actualiza la página (F5 o Ctrl+R)
3. Limpia caché del navegador
4. Prueba con otro navegador
5. Contacta soporte técnico

### 5.2 Consejos para Mejor Calidad de Audio

✅ **Ambiente ideal:**
- Habitación silenciosa
- Sin música o TV de fondo
- Evita áreas con eco

✅ **Técnica de grabación:**
- Mantén distancia constante del micrófono (15-20 cm)
- Habla con tono natural y pausado
- No cubras el micrófono con la mano

✅ **Equipamiento:**
- Auriculares con micrófono integrado (recomendado)
- Micrófono USB de buena calidad
- Evita micrófonos muy económicos

---

## 6. Preguntas Frecuentes

### ¿Es seguro este sistema?

**Sí**. Tu voz se convierte en un patrón matemático único (embedding) que se almacena encriptado. Nadie puede reconstruir tu voz a partir de estos datos.

### ¿Puede alguien suplantar mi voz con una grabación?

**No**. El sistema incluye tecnología anti-suplantación que detecta grabaciones y voces sintéticas.

### ¿Qué pasa si estoy resfriado o ronco?

El sistema es robusto a cambios naturales de voz, pero si tu voz cambia drásticamente (ej: laringitis severa), podrías tener problemas temporales de verificación. Realiza un nuevo enrollment cuando te recuperes si es necesario.

### ¿Puedo usar el sistema en mi teléfono móvil?

Sí, siempre que uses un navegador web compatible y tengas micrófono funcional.

### ¿Cuántas veces puedo fallar la verificación?

No hay límite de intentos para verificación de voz. Sin embargo, tras múltiples intentos fallidos de login con contraseña, tu cuenta se bloqueará temporalmente (15 minutos).

### ¿Puedo eliminar mi perfil biométrico?

Sí, contacta a tu administrador o ve a Configuración → Privacidad → Eliminar perfil biométrico.

### ¿El sistema funciona en cualquier idioma?

El sistema está optimizado para **español**, pero puede funcionar con otros idiomas con menor precisión.

---

## 7. Seguridad y Privacidad

### 7.1 Cómo Protegemos Tu Voz

🔒 **Encriptación**: Tus datos biométricos se almacenan encriptados  
🚫 **No se guarda audio**: Solo patrones matemáticos (embeddings)  
🔐 **Acceso controlado**: Solo personal autorizado puede acceder  
📝 **Auditoría**: Todas las acciones se registran  
🛡️ **Anti-suplantación**: Detección de ataques de replay

### 7.2 Buenas Prácticas de Seguridad

✅ **Contraseña segura**: Usa contraseñas únicas y complejas  
✅ **No compartas tu cuenta**: Cada usuario debe tener su propia cuenta  
✅ **Cierra sesión**: Especialmente en computadoras compartidas  
✅ **Reporta anomalías**: Si notas actividad sospechosa, contacta al admin  
✅ **Actualiza tu navegador**: Mantén tu navegador actualizado

### 7.3 Derechos del Usuario

Tienes derecho a:
- **Acceder** a tus datos biométricos
- **Eliminar** tu perfil de voz
- **Exportar** tu información personal
- **Revocar** el consentimiento en cualquier momento

**Para ejercer tus derechos**: Contacta al administrador del sistema.

---

## 📞 Soporte y Contacto

¿Necesitas ayuda adicional?

- **Administrador del sistema**: [Contacto interno de tu organización]
- **Soporte técnico**: [Email o teléfono de soporte]

---

## 📄 Notas Finales

**Versión del manual**: 1.0.0  
**Última actualización**: Diciembre 2024  
**Compatible con**: Sistema de Biometría de Voz v1.0.0

**Registro de cambios**:
- v1.0.0 (Dic 2024): Versión inicial del manual

---

*Este manual fue creado para facilitar el uso del sistema de autenticación por biometría de voz. Para información técnica detallada, consulta la documentación técnica del sistema.*
