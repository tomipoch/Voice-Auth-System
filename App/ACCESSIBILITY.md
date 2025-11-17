# Accessibility Guide

## ♿ Overview

VoiceAuth está diseñado para ser completamente accesible siguiendo las pautas WCAG 2.1 Level AA.

## 🎯 Standards & Compliance

### WCAG 2.1 Level AA

- ✅ **Perceivable**: Información presentada de manera que todos los usuarios puedan percibirla
- ✅ **Operable**: Interfaz navegable por teclado y otros dispositivos
- ✅ **Understandable**: Información y operación clara y predecible
- ✅ **Robust**: Compatible con tecnologías asistivas

### ARIA Compliance

Uso correcto de atributos ARIA:

- `aria-label` y `aria-labelledby` para elementos sin texto visible
- `aria-describedby` para descripciones adicionales
- `aria-live` para anuncios dinámicos
- `role` para semántica adicional

## ⌨️ Keyboard Navigation

### Global Shortcuts

```
Tab: Navegar hacia adelante
Shift+Tab: Navegar hacia atrás
Enter/Space: Activar botones y links
Escape: Cerrar modales y menús
Arrow Keys: Navegación en menús y listas
```

### Skip Links

```jsx
// Primer elemento en la página
<SkipLink />

// Permite saltar al contenido principal
// Visible solo al recibir foco con Tab
```

**Implementación:**

```jsx
<a href="#main-content" className="sr-only focus:not-sr-only">
  Saltar al contenido principal
</a>
```

### Focus Management

#### Trampas de Foco (Focus Traps)

Para modales y diálogos:

```javascript
import { trapFocus, restoreFocus } from './hooks/useAccessibility';

const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement;
      const cleanup = trapFocus(modalRef);
      return () => {
        cleanup();
        restoreFocus(previousFocusRef);
      };
    }
  }, [isOpen]);

  return (
    <div ref={modalRef} role="dialog" aria-modal="true">
      {children}
    </div>
  );
};
```

#### Focus Visible

Solo mostrar outline cuando se navega con teclado:

```css
/* No outline en click de mouse */
*:focus {
  outline: none;
}

/* Outline solo con teclado */
*:focus-visible {
  outline: 2px solid theme('colors.blue.500');
  outline-offset: 2px;
}
```

## 🔊 Screen Readers

### Screen-Reader Only Content

Clase `.sr-only` para contenido solo para lectores de pantalla:

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Uso:**

```jsx
<button>
  <TrashIcon />
  <span className="sr-only">Eliminar usuario</span>
</button>
```

### Live Regions

Anunciar cambios dinámicos:

```javascript
import { useAnnounce } from './hooks/useAccessibility';

const Component = () => {
  const announce = useAnnounce();

  const handleSave = async () => {
    await save();
    announce('Los cambios se han guardado exitosamente', 'polite');
  };

  return <button onClick={handleSave}>Guardar</button>;
};
```

**Niveles de prioridad:**

```javascript
// Polite: Espera a que el lector termine
announce('Mensaje informativo', 'polite');

// Assertive: Interrumpe inmediatamente
announce('Error crítico', 'assertive');
```

### ARIA Labels

#### Botones con solo iconos

```jsx
<button aria-label="Cerrar modal">
  <XIcon />
</button>
```

#### Links descriptivos

```jsx
{
  /* ❌ Mal */
}
<a href="/profile">Click aquí</a>;

{
  /* ✅ Bien */
}
<a href="/profile">Ver perfil de usuario</a>;
```

#### Formularios

```jsx
<label htmlFor="email">
  Correo electrónico
</label>
<input
  id="email"
  type="email"
  aria-required="true"
  aria-invalid={errors.email ? 'true' : 'false'}
  aria-describedby="email-error"
/>
{errors.email && (
  <span id="email-error" className="text-red-500">
    {errors.email}
  </span>
)}
```

## 🎨 Visual Accessibility

### Color Contrast

Ratios mínimos WCAG AA:

- **Texto normal**: 4.5:1
- **Texto grande** (18pt+): 3:1
- **Iconos UI**: 3:1

```css
/* Ejemplo de contraste adecuado */
.button-primary {
  background-color: #1d4ed8; /* Blue-700 */
  color: #ffffff; /* White */
  /* Ratio: 8.6:1 ✅ */
}
```

### High Contrast Mode

Soporte para modo de alto contraste:

```css
@media (prefers-contrast: high) {
  * {
    border-color: currentColor !important;
  }

  .button {
    border: 2px solid currentColor;
  }

  .card {
    outline: 2px solid currentColor;
  }
}
```

### Color Independence

No usar solo color para comunicar información:

```jsx
{
  /* ❌ Mal: Solo color */
}
<span className="text-red-500">Error</span>;

{
  /* ✅ Bien: Color + icono + texto */
}
<span className="flex items-center gap-2 text-red-500">
  <AlertIcon />
  <span>Error: El campo es requerido</span>
</span>;
```

### Focus Indicators

Indicadores de foco claramente visibles:

```css
button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}
```

## 🎭 Motion & Animation

### Reduced Motion

Respetar preferencia de reducir movimiento:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**En JavaScript:**

```javascript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (!prefersReducedMotion) {
  // Aplicar animaciones
  element.classList.add('animate-fade-in');
}
```

### Animation Guidelines

```css
/* DO ✅ */
.fade-in {
  animation: fadeIn 0.3s ease-in;
}

/* DON'T ❌ */
.flash {
  animation: flash 0.1s infinite; /* Puede causar convulsiones */
}
```

**Evitar:**

- Flashes más de 3 veces por segundo
- Animaciones infinitas agresivas
- Parallax excesivo

## 📱 Touch & Mobile

### Touch Target Sizing

Tamaño mínimo de 44x44px:

```css
button,
a,
input[type='checkbox'],
input[type='radio'] {
  min-width: 44px;
  min-height: 44px;
  /* O usar padding para llegar a 44px */
}
```

### Touch Gestures

Proporcionar alternativas a gestures complejos:

```jsx
{
  /* ❌ Solo swipe */
}
<div onSwipe={handleSwipe}>...</div>;

{
  /* ✅ Swipe + botones */
}
<div>
  <button onClick={handlePrev}>Anterior</button>
  <SwipeableArea onSwipe={handleSwipe}>...</SwipeableArea>
  <button onClick={handleNext}>Siguiente</button>
</div>;
```

## 🛠️ Accessibility Hooks

### useAccessibility.js

#### 1. Focus Trap

```javascript
const cleanup = trapFocus(containerRef);
// Mantiene foco dentro del contenedor
// Llama cleanup() para liberar
```

#### 2. Restore Focus

```javascript
const previousFocusRef = useRef(document.activeElement);
// ... después de cerrar modal
restoreFocus(previousFocusRef);
```

#### 3. Announce

```javascript
const announce = useAnnounce();
announce('Mensaje para screen reader', 'polite');
```

#### 4. Focus Visible

```javascript
const { isFocusVisible } = useFocusVisible();

<button className={isFocusVisible ? 'focus-ring' : ''} {...props} />;
```

#### 5. High Contrast Mode

```javascript
const isHighContrast = useHighContrastMode();

<div className={isHighContrast ? 'high-contrast-styles' : ''}>{children}</div>;
```

## 📋 Semantic HTML

### Usar elementos correctos

```jsx
{
  /* ❌ Mal */
}
<div onClick={handleClick}>Click me</div>;

{
  /* ✅ Bien */
}
<button onClick={handleClick}>Click me</button>;

{
  /* ❌ Mal */
}
<div className="heading">Título</div>;

{
  /* ✅ Bien */
}
<h2>Título</h2>;

{
  /* ❌ Mal */
}
<span onClick={navigate}>Ver más</span>;

{
  /* ✅ Bien */
}
<a href="/more">Ver más</a>;
```

### Landmarks

Estructura semántica con landmarks:

```jsx
<body>
  <SkipLink />

  <header role="banner">
    <nav aria-label="Navegación principal">...</nav>
  </header>

  <main id="main-content" role="main">
    <article>...</article>
    <aside role="complementary">...</aside>
  </main>

  <footer role="contentinfo">...</footer>
</body>
```

## 🧪 Testing

### Automated Testing

```bash
# Instalar herramientas
npm install --save-dev @axe-core/react jest-axe

# Correr tests de accesibilidad
npm run test:a11y
```

**Ejemplo de test:**

```javascript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('should not have accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Manual Testing

#### Checklist

- [ ] Navegación completa con teclado
- [ ] Probar con screen reader (NVDA/JAWS/VoiceOver)
- [ ] Verificar contraste de colores
- [ ] Zoom al 200% sin pérdida de contenido
- [ ] Modo alto contraste funcional
- [ ] Animaciones respetan `prefers-reduced-motion`
- [ ] Formularios con labels y errores claros
- [ ] Mensajes de error descriptivos
- [ ] Touch targets de 44x44px mínimo

#### Screen Readers

**Windows:**

- NVDA (gratis)
- JAWS

**macOS:**

- VoiceOver (integrado)

**Linux:**

- Orca

**Mobile:**

- TalkBack (Android)
- VoiceOver (iOS)

### Browser Extensions

- **axe DevTools**: Auditoría automatizada
- **WAVE**: Evaluación visual de accesibilidad
- **Lighthouse**: Auditoría integral (incluye a11y)
- **Color Contrast Analyzer**: Verificar contraste

## 📚 Components Examples

### Accessible Modal

```jsx
<Modal
  isOpen={isOpen}
  onClose={onClose}
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">Título del Modal</h2>
  <p id="modal-description">Descripción del contenido</p>

  <button onClick={handleSave}>Guardar</button>
  <button onClick={onClose}>Cancelar</button>
</Modal>
```

### Accessible Form

```jsx
<form onSubmit={handleSubmit} noValidate>
  <div>
    <label htmlFor="name">
      Nombre completo
      <abbr title="requerido" aria-label="requerido">
        *
      </abbr>
    </label>
    <input
      id="name"
      type="text"
      required
      aria-required="true"
      aria-invalid={errors.name ? 'true' : 'false'}
      aria-describedby={errors.name ? 'name-error' : undefined}
    />
    {errors.name && (
      <span id="name-error" role="alert" className="text-red-500">
        {errors.name}
      </span>
    )}
  </div>

  <button type="submit">Enviar</button>
</form>
```

### Accessible Table

```jsx
<table>
  <caption>Lista de usuarios registrados</caption>
  <thead>
    <tr>
      <th scope="col">Nombre</th>
      <th scope="col">Email</th>
      <th scope="col">Acciones</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Juan Pérez</th>
      <td>juan@example.com</td>
      <td>
        <button aria-label="Editar usuario Juan Pérez">
          <EditIcon />
        </button>
        <button aria-label="Eliminar usuario Juan Pérez">
          <TrashIcon />
        </button>
      </td>
    </tr>
  </tbody>
</table>
```

## 🎯 Best Practices

### DO ✅

- Usar HTML semántico
- Proporcionar labels a todos los inputs
- Navegación completa por teclado
- Indicadores de foco visibles
- Textos alternativos en imágenes
- Contraste adecuado (mínimo 4.5:1)
- Anuncios para contenido dinámico
- Respetar preferencias del usuario (motion, contrast)
- Probar con lectores de pantalla
- Implementar skip links

### DON'T ❌

- No usar solo color para comunicar
- No eliminar outlines sin alternativa
- No crear keyboard traps
- No usar `tabindex` positivo
- No poner texto en imágenes
- No auto-reproducir audio/video
- No usar flashes rápidos
- No ignorar errores de validación HTML
- No asumir que todos usan mouse
- No omitir texto alternativo

## 📊 Accessibility Audit

### Lighthouse Scores

Target: **95+**

```bash
npm run build
npx lighthouse http://localhost:4173 --view
```

### Axe DevTools

```bash
npm install --save-dev @axe-core/cli

npx axe http://localhost:5173
```

## 🔗 Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)
- [Inclusive Components](https://inclusive-components.design/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

## 🚀 Future Enhancements

1. **Voice Commands**: Control por voz para usuarios con movilidad reducida
2. **Dyslexia-Friendly Font**: Opción de fuente OpenDyslexic
3. **Text-to-Speech**: Lectura automática de contenido
4. **Customizable UI**: Tamaño de fuente, espaciado, colores personalizables
5. **Braille Display Support**: Soporte para displays braille

---

**Diseñado para ser accesible a todos** ♿
