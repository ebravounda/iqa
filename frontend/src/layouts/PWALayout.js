import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { QrCode, User, Calendar, Bell, UserPlus, Sun, Moon } from 'lucide-react';
import { useState, useEffect } from 'react';

const navItems = [
  { path: '/app', icon: QrCode, label: 'QR' },
  { path: '/app/classes', icon: Calendar, label: 'Clases' },
  { path: '/app/guests', icon: UserPlus, label: 'Invitados' },
  { path: '/app/notifications', icon: Bell, label: 'Avisos' },
  { path: '/app/profile', icon: User, label: 'Perfil' },
];

export const PWALayout = ({ children }) => {
  const { gym, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('ingresoqr-theme') || 'dark');

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
    localStorage.setItem('ingresoqr-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
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
    <div className="min-h-screen min-h-[100dvh]" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-40 backdrop-blur-xl" style={{ background: 'var(--bg-primary)', borderBottom: '1px solid var(--border-primary)' }}>
        <div className="flex items-center justify-between max-w-lg mx-auto px-4 py-3 sm:py-4">
          <div className="flex items-center gap-3 min-w-0">
            {gym?.logo_url ? (
              <img 
                src={gym.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${gym.logo_url}` : gym.logo_url} 
                alt={gym.name} 
                className="h-9 sm:h-10 max-w-[120px] object-contain shrink-0"
              />
            ) : (
              <div 
                className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center font-black text-base sm:text-lg shrink-0"
                style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
              >
                {gym?.name?.charAt(0) || 'G'}
              </div>
            )}
            <div className="min-w-0">
              <h1 className="font-bold text-sm truncate">{gym?.name || 'IngresoQR'}</h1>
              <p className="text-[10px] sm:text-xs" style={{ color: 'var(--text-muted)' }}>Socio</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 ml-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg transition-colors"
              style={{ color: 'var(--text-secondary)' }}
              data-testid="pwa-theme-toggle-btn"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              onClick={handleLogout}
              className="text-xs sm:text-sm"
              style={{ color: 'var(--text-muted)' }}
              data-testid="pwa-logout-btn"
            >
              Salir
            </button>
          </div>
        </div>
      </header>

      {/* Install prompt banner */}
      {showInstallPrompt && (
        <div className="fixed top-16 left-3 right-3 z-50 max-w-lg mx-auto">
          <div className="rounded-xl p-3 sm:p-4 flex items-center gap-3" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-secondary)' }}>
            <div 
              className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: 'var(--gym-primary)' }}
            >
              <QrCode size={20} className="text-black" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-xs sm:text-sm">Crear Acceso Directo</p>
              <p className="text-[10px] sm:text-xs" style={{ color: 'var(--text-muted)' }}>Accede más rápido</p>
            </div>
            <button
              onClick={handleInstall}
              className="btn-gym-primary text-xs py-1.5 px-3 sm:py-2 sm:px-4 shrink-0"
              data-testid="install-pwa-btn"
            >
              Instalar
            </button>
            <button
              onClick={() => setShowInstallPrompt(false)}
              className="p-1 shrink-0"
              style={{ color: 'var(--text-muted)' }}
            >
              <span className="text-lg leading-none">&times;</span>
            </button>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="pwa-content pt-16 sm:pt-[72px] px-3 sm:px-4">
        <div className="max-w-lg mx-auto py-4 sm:py-6">
          {children}
        </div>
      </main>

      {/* Bottom navigation */}
      <nav className="pwa-bottom-nav" data-testid="pwa-bottom-nav">
        <div className="max-w-lg mx-auto h-full flex items-center justify-around px-1 sm:px-4">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className="flex flex-col items-center gap-0.5 py-1.5 px-2 sm:px-4 rounded-xl transition-colors"
                style={isActive 
                  ? { color: 'var(--text-primary)' }
                  : { color: 'var(--text-muted)' }
                }
                data-testid={`pwa-nav-${item.label.toLowerCase()}`}
              >
                <div className="p-1.5 sm:p-2 rounded-xl" style={isActive ? { background: 'var(--bg-tertiary)' } : {}}>
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                </div>
                <span className="text-[10px] sm:text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
