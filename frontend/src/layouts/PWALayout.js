import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { QrCode, User, CreditCard, History, Plus, Calendar } from 'lucide-react';
import { useState, useEffect } from 'react';

const navItems = [
  { path: '/app', icon: QrCode, label: 'QR' },
  { path: '/app/classes', icon: Calendar, label: 'Clases' },
  { path: '/app/history', icon: History, label: 'Historial' },
  { path: '/app/membership', icon: CreditCard, label: 'Membresía' },
  { path: '/app/profile', icon: User, label: 'Perfil' },
];

export const PWALayout = ({ children }) => {
  const { gym, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Only show if not already installed
      if (!window.matchMedia('(display-mode: standalone)').matches) {
        setShowInstallPrompt(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setShowInstallPrompt(false);
    }
    setDeferredPrompt(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/app/login');
  };

  return (
    <div className="min-h-screen bg-[#09090B]">
      {/* Header */}
      <header className="glass-dark fixed top-0 left-0 right-0 z-40 px-6 py-4">
        <div className="flex items-center justify-between max-w-lg mx-auto">
          <div className="flex items-center gap-3">
            {gym?.logo_url ? (
              <img 
                src={gym.logo_url} 
                alt={gym.name} 
                className="w-10 h-10 rounded-lg object-cover"
              />
            ) : (
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center font-black text-lg"
                style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
              >
                {gym?.name?.charAt(0) || 'G'}
              </div>
            )}
            <div>
              <h1 className="font-bold text-sm">{gym?.name || 'GymAccess'}</h1>
              <p className="text-xs text-zinc-500">Socio</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-zinc-500 hover:text-white text-sm"
            data-testid="pwa-logout-btn"
          >
            Salir
          </button>
        </div>
      </header>

      {/* Install prompt banner */}
      {showInstallPrompt && (
        <div className="fixed top-20 left-4 right-4 z-50 max-w-lg mx-auto">
          <div className="install-highlight rounded-xl">
            <div className="relative z-10 bg-zinc-900 rounded-xl p-4 flex items-center gap-4">
              <div 
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: 'var(--gym-primary)' }}
              >
                <Plus size={24} className="text-black" />
              </div>
              <div className="flex-1">
                <p className="font-bold text-sm">Crear Acceso Directo</p>
                <p className="text-xs text-zinc-400">Accede más rápido desde tu pantalla</p>
              </div>
              <button
                onClick={handleInstall}
                className="btn-gym-primary text-sm py-2 px-4"
                data-testid="install-pwa-btn"
              >
                Instalar
              </button>
              <button
                onClick={() => setShowInstallPrompt(false)}
                className="text-zinc-500 p-1"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="pwa-content pt-20 px-4">
        <div className="max-w-lg mx-auto py-6">
          {children}
        </div>
      </main>

      {/* Bottom navigation */}
      <nav className="pwa-bottom-nav" data-testid="pwa-bottom-nav">
        <div className="max-w-lg mx-auto h-full flex items-center justify-around px-4">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center gap-1 py-2 px-4 rounded-xl transition-colors ${
                  isActive 
                    ? 'text-white' 
                    : 'text-zinc-500 hover:text-zinc-300'
                }`}
                data-testid={`pwa-nav-${item.label.toLowerCase()}`}
              >
                <div className={`p-2 rounded-xl ${isActive ? 'bg-zinc-800' : ''}`}>
                  <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                </div>
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
