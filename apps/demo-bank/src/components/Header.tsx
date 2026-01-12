import { useNavigate, useLocation } from 'react-router-dom';
import { Building2, Bell, LogOut, User } from 'lucide-react';
import authService from '../services/authService';
import toast from 'react-hot-toast';

interface HeaderProps {
  showNav?: boolean;
  isEnrolled?: boolean;
}

export default function Header({ showNav = true, isEnrolled = false }: HeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getUser();

  const handleLogout = () => {
    authService.logout();
    toast.success('Sesión cerrada');
    navigate('/');
  };

  const navItems = [
    { label: 'Inicio', path: '/dashboard' },
    { label: 'Transferir', path: '/transfer', requiresEnrollment: true },
    { label: 'Perfil', path: '/profile' },
  ];

  const handleNavClick = (item: typeof navItems[0]) => {
    if (item.requiresEnrollment && !isEnrolled) {
      toast.error('Primero activa la seguridad biométrica');
      return;
    }
    navigate(item.path);
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-linear-to-r from-[#1a365d] to-[#2c5282] text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-3 hover:opacity-90 transition-opacity"
            >
              <div className="w-10 h-10 bg-white/10 backdrop-blur-sm rounded-lg flex items-center justify-center border border-white/20">
                <Building2 className="w-6 h-6 text-[#f6ad55]" />
              </div>
              <div className="text-left">
                <h1 className="font-bold text-lg">Banco Pirulete</h1>
                <p className="text-blue-200/70 text-xs">Banca en Línea</p>
              </div>
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="relative p-2 hover:bg-white/10 rounded-lg transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-[#f6ad55] rounded-full" />
            </button>
            <button 
              onClick={() => navigate('/profile')}
              className="flex items-center gap-3 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg border border-white/10 transition-colors cursor-pointer"
            >
              <div className="w-8 h-8 rounded-full bg-linear-to-br from-[#f6ad55] to-[#ed8936] flex items-center justify-center text-xs font-bold text-[#1a365d]">
                {user?.first_name?.[0] || 'T'}
              </div>
              <span className="text-sm hidden sm:block">Hola, {user?.first_name || 'Tomás'}</span>
            </button>
            <button onClick={handleLogout} className="p-2 hover:bg-white/10 rounded-lg transition-colors" title="Salir">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      {showNav && (
        <div className="bg-[#1a365d]/50 border-t border-white/10">
          <div className="max-w-7xl mx-auto px-6">
            <nav className="flex gap-1 overflow-x-auto py-2">
              {navItems.map((item) => (
                <button 
                  key={item.label}
                  onClick={() => handleNavClick(item)}
                  className={`px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-colors ${
                    isActive(item.path) 
                      ? 'bg-[#f6ad55] text-[#1a365d] font-semibold' 
                      : 'hover:bg-white/10 text-white/80'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}
    </header>
  );
}
