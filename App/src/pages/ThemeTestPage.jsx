import { useTheme } from '../hooks/useTheme';

const ThemeTestPage = () => {
  const { theme, changeTheme, isDark } = useTheme();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 dark:bg-gray-900 transition-colors duration-300">
      <div className="p-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
          Test del Modo Oscuro
        </h1>
        
        <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg mb-6">
          <p className="text-gray-800 dark:text-gray-200 mb-4">
            Tema actual: {theme}
          </p>
          <p className="text-gray-800 dark:text-gray-200 mb-4">
            Estado isDark: {isDark ? 'true' : 'false'}
          </p>
          <p className="text-gray-800 dark:text-gray-200 mb-4">
            Clase HTML actual: {document.documentElement.classList.toString()}
          </p>
        </div>

        <div className="space-x-4">
          <button 
            onClick={() => changeTheme('light')}
            className="px-4 py-2 bg-blue-500 dark:bg-blue-600 text-white rounded hover:bg-blue-600 dark:hover:bg-blue-700"
          >
            Tema Claro
          </button>
          <button 
            onClick={() => changeTheme('dark')}
            className="px-4 py-2 bg-gray-800 dark:bg-gray-700 text-white rounded hover:bg-gray-900 dark:hover:bg-gray-600"
          >
            Tema Oscuro
          </button>
          <button 
            onClick={() => changeTheme('auto')}
            className="px-4 py-2 bg-purple-500 dark:bg-purple-600 text-white rounded hover:bg-purple-600 dark:hover:bg-purple-700"
          >
            Automático
          </button>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-900 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 dark:border-gray-700 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Tarjeta de Prueba
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Este es un texto de prueba para ver el contraste en modo oscuro.
            </p>
          </div>
          
          <div className="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
              Elemento Azul
            </h3>
            <p className="text-blue-700 dark:text-blue-300">
              Componente con colores azules para probar el contraste.
            </p>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
              Elemento Verde
            </h3>
            <p className="text-green-700 dark:text-green-300">
              Componente con colores verdes para probar el contraste.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeTestPage;