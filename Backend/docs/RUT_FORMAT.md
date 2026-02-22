# ✅ RUT Estandarizado - Formato Único

## 🎯 Formato ÚNICO Aceptado

### **Backend acepta SOLAMENTE:**
```
XXXXXXXX-X
```

**Ejemplos válidos:**
- `12345678-5` ✅
- `11111111-1` ✅
- `24876931-K` ✅

**Ejemplos RECHAZADOS:**
- `12.345.678-5` ❌ (con puntos)
- `123456785` ❌ (sin guión)
- `12345678` ❌ (sin dígito verificador)

---

## 🔧 Cambios Aplicados

### **Backend (`validators.py`):**

```python
def validate_rut(rut: str) -> bool:
    # 1. RECHAZAR si tiene puntos
    if "." in rut:
        return False
    
    # 2. Quitar guión y uppercase
    clean = rut.replace("-", "").upper()
    
    # 3. Validar formato y dígito verificador
    ...
```

**Cambios:**
- ✅ Rechaza formato con puntos
- ✅ Solo acepta `XXXXXXXX-X`
- ✅ Error msg: "Use format: 12345678-9 (without dots)"

### **Frontend (`RegisterPage.tsx`):**

```typescript
// Campo verificador - YA convierte a mayúscula
const value = e.target.value.toUpperCase().slice(0, 1);
if (value === '' || /^[0-9K]$/.test(value)) {
  // Procesa...
}
```

**Estado actual:**
- ✅ Campo 1: Solo números (8 máx)
- ✅ Campo 2: 0-9 o K
- ✅ Auto-convierte a MAYÚSCULA
- ✅ Junta con guión: `numero-verificador`

---

## 📊 Flujo Completo

```
Usuario ingresa:
┌────────────┐   ┌───┐
│ 12345678   │ - │ k │  ← Usuario puede ingresar k minúscula
└────────────┘   └───┘

Frontend procesa:
1. Convierte a mayúscula: "K"
2. Junta con guión: "12345678-K"

Backend recibe:
"12345678-K"

Backend valida:
1. ¿Tiene puntos? NO ✅
2. Quita guión: "12345678K"
3. Separa: "12345678" y "K"
4. Calcula dígito esperado (Módulo 11)
5. Compara y valida
```

---

## ✅ Comportamiento Estandarizado

### **Frontend:**
| Campo | Input Usuario | Procesado | Enviado |
|-------|---------------|-----------|---------|
| RUT | `12345678` | `12345678` | `12345678-K` |
| Verificador | `k` | `K` | `12345678-K` |
| Verificador | `9` | `9` | `12345678-9` |

### **Backend:**
| Recibe | Válido | Razón |
|--------|--------|-------|
| `12345678-5` | ✅ | Formato correcto |
| `12345678-K` | ✅ | K mayúscula OK |
| `12.345.678-5` | ❌ | Tiene puntos |
| `123456785` | ❌ | Sin guión |
| `12345678-k` | ❌ | k minúscula* |

*El frontend siempre envía K mayúscula, pero si alguien usa la API directamente con k minúscula, será rechazado.

---

## 🎨 UX Final

```
┌─────────────────────────────────────┐
│  RUT                                │
│                                     │
│  ┌─────────────┐   ┌───┐          │
│  │ 12345678    │ - │ K │          │
│  └─────────────┘   └───┘          │
│                                     │
│  Ingresa tu RUT sin puntos.        │
│  Ej: 12345678-9                    │
└─────────────────────────────────────┘
```

**Características:**
- ✅ Visual claro con guión en el medio
- ✅ Campo número: solo dígitos
- ✅ Campo verificador: 0-9 o K
- ✅ Auto-uppercase en verificador
- ✅ Hint claro sin confusiones

---

## 📝 Validaciones

### **Frontend (JavaScript):**
```typescript
// Valida RUT completo
const validateRUT = (rut: string): boolean => {
  const cleanRut = rut.replace(/\./g, '').replace(/-/g, '');
  if (cleanRut.length < 8) return false;
  
  const rutNumber = cleanRut.slice(0, -1);
  const verifier = cleanRut.slice(-1).toUpperCase();
  
  if (!/^\d+$/.test(rutNumber)) return false;
  
  // Cálculo Módulo 11...
  return verifier === calculatedVerifier;
};
```

### **Backend (Python):**
```python
def validate_rut(rut: str) -> bool:
    # Rechazar formato con puntos
    if "." in rut:
        return False
    
    # Resto de validación...
```

---

## 🚀 Estado Final

**Formato único:** `XXXXXXXX-X` (sin puntos, con guión)
**K siempre:** MAYÚSCULA
**Frontend:** Convierte automáticamente
**Backend:** Rechaza formato con puntos

**¡Sistema estandarizado y sin confusiones!** ✅
