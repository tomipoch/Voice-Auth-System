/**
 * SkipLink - Componente de accesibilidad para saltar al contenido principal
 * Permite a usuarios de teclado/lectores de pantalla omitir la navegación
 */
const SkipLink = () => {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-6 focus:py-3 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-4 focus:ring-blue-500/50 transition-all"
    >
      Saltar al contenido principal
    </a>
  );
};

export default SkipLink;
