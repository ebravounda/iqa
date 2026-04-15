import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useBusiness } from '../context/BusinessContext';
import { 
  LayoutDashboard, Users, CreditCard, Building2, UserCog, Settings, 
  Calendar, Clock, Bell, Shield, QrCode, Menu, X, ChevronLeft,
  LogOut, Smartphone, UserCheck, DollarSign, Mail, ShoppingCart,
  Layers, Code, Megaphone, BarChart3, ClipboardList, Database, Monitor, Trophy, Dumbbell,
  Sun, Moon, AlertOctagon
} from 'lucide-react';

const getNavItems = (role, isImpersonating, permissions, labels) => {
  // When impersonating, show gym_admin menu
  const effectiveRole = isImpersonating ? 'gym_admin' : role;

  const items = [
    { path: '/admin', icon: LayoutDashboard, label: 'Dashboard', roles: ['super_admin', 'gym_admin', 'gym_manager', 'trainer'] },
    { path: '/admin/members', icon: Users, label: labels.members, roles: ['super_admin', 'gym_admin', 'gym_manager'], perm: 'members_view' },
    { path: '/admin/plans', icon: CreditCard, label: labels.plans, roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/pos', icon: ShoppingCart, label: labels.pos, roles: ['super_admin', 'gym_admin', 'gym_manager'], perm: 'pos_sell' },
    { path: '/admin/classes', icon: Calendar, label: labels.classes, roles: ['super_admin', 'gym_admin', 'gym_manager'], perm: 'classes_manage' },
    { path: '/admin/attendance', icon: UserCheck, label: labels.attendance, roles: ['super_admin', 'gym_admin', 'gym_manager', 'trainer'] },
    { path: '/admin/schedules', icon: Clock, label: labels.schedules, roles: ['super_admin', 'gym_admin', 'gym_manager', 'trainer'] },
    { path: '/admin/access', icon: Shield, label: labels.accesses, roles: ['super_admin', 'gym_admin', 'gym_manager'], perm: 'access_view' },
    { path: '/admin/accounting', icon: DollarSign, label: 'Contabilidad', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/analytics', icon: BarChart3, label: 'Analytics', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/forms', icon: ClipboardList, label: 'Formularios', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/data', icon: Database, label: 'Datos', roles: ['super_admin', 'gym_admin', 'gym_manager'], perm: 'data_export' },
    { path: '/admin/staff', icon: UserCog, label: 'Personal', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/iframes', icon: Code, label: 'Iframes', roles: ['gym_admin'] },
    { path: '/admin/devices', icon: Smartphone, label: 'Dispositivos', roles: ['super_admin'] },
    { path: '/admin/device-monitor', icon: Monitor, label: 'Monitor RPi', roles: ['super_admin'] },
    { path: '/admin/security', icon: Shield, label: 'Seguridad', roles: ['super_admin'] },
    { path: '/admin/gamification', icon: Trophy, label: labels.gamification, roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/routines', icon: Dumbbell, label: labels.routines, roles: ['super_admin', 'gym_admin', 'trainer'] },
    { path: '/admin/templates', icon: Mail, label: 'Plantillas Email', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/notifications', icon: Bell, label: 'Notificaciones', roles: ['super_admin', 'gym_admin', 'gym_manager'], perm: 'notifications_send' },
    { path: '/admin/broadcast', icon: Megaphone, label: 'Comunicados', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/gyms', icon: Building2, label: 'Negocios', roles: ['super_admin'] },
    { path: '/admin/saas-plans', icon: Layers, label: 'Planes SaaS', roles: ['super_admin'] },
    { path: '/admin/settings', icon: Settings, label: 'Configuracion', roles: ['super_admin', 'gym_admin'] },
  ];

  const defaultPerms = ["members_view", "members_create", "members_edit", "payments_register", "pos_sell", "access_view", "classes_manage"];
  const perms = effectiveRole === 'gym_manager' ? (permissions || defaultPerms) : null;

  return items.filter(item => {
    if (!item.roles.includes(effectiveRole)) return false;
    if (perms && item.perm && !perms.includes(item.perm)) return false;
    return true;
  });
};

export const AdminLayout = ({ children }) => {
  const { admin, logout, isImpersonating, exitImpersonation } = useAuth();
  const { labels } = useBusiness();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('ingresoqr-theme') || 'dark');
  const [gymData, setGymData] = useState(null);

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
    localStorage.setItem('ingresoqr-theme', theme);
  }, [theme]);

  // Apply corporate colors from gym and store gym data for logo
  useEffect(() => {
    if (admin?.gym_id) {
      const API = process.env.REACT_APP_BACKEND_URL + '/api';
      fetch(`${API}/gyms/${admin.gym_id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      }).then(r => r.json()).then(gym => {
        setGymData(gym);
        if (gym?.primary_color) document.documentElement.style.setProperty('--gym-primary', gym.primary_color);
        if (gym?.bg_color) document.documentElement.style.setProperty('--admin-bg', gym.bg_color);
        if (gym?.menu_color) document.documentElement.style.setProperty('--admin-menu', gym.menu_color);
        if (gym?.text_color) document.documentElement.style.setProperty('--admin-text', gym.text_color);
        if (gym?.secondary_color) document.documentElement.style.setProperty('--gym-secondary', gym.secondary_color);
      }).catch(() => {});
    }
  }, [admin?.gym_id]);

  const gymLogoUrl = gymData?.logo_url 
    ? (gymData.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${gymData.logo_url}` : gymData.logo_url)
    : null;

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');
  
  const navItems = getNavItems(admin?.role, isImpersonating, admin?.permissions, labels);

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const handleExitImpersonation = () => {
    exitImpersonation();
    navigate('/admin/gyms');
  };

  // Payment suspended - block all modules
  if (admin?.gym_status === 'payment_suspended' && admin?.role !== 'super_admin' && !isImpersonating) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
        <div className="max-w-md w-full text-center space-y-6" data-testid="payment-suspended-screen">
          <div className="w-24 h-24 rounded-full bg-orange-500/10 border-2 border-orange-500/40 flex items-center justify-center mx-auto">
            <AlertOctagon size={48} className="text-orange-500" />
          </div>
          <div>
            <h1 className="text-2xl font-black mb-2">Cuenta Suspendida</h1>
            <p className="text-lg font-semibold text-orange-400">por falta de pago</p>
          </div>
          <div className="p-4 rounded-xl" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
            <p style={{ color: 'var(--text-secondary)' }}>
              Tu cuenta ha sido suspendida temporalmente debido a un pago pendiente. 
              Todos los modulos y accesos estan bloqueados hasta que se regularice la situacion.
            </p>
          </div>
          <div className="p-4 rounded-xl" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-secondary)' }}>
            <p className="text-sm font-medium mb-1">Contacta a Soporte</p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Escribe a <strong>soporte@ingresoqr.com</strong> o comunicate con tu representante para resolver esta situacion.
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="px-6 py-3 rounded-xl text-sm font-semibold transition-colors"
            style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: '1px solid var(--border-secondary)' }}
            data-testid="suspended-logout-btn"
          >
            <LogOut size={16} className="inline mr-2" /> Cerrar Sesion
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Impersonation Banner */}
      {isImpersonating && (
        <div className="fixed top-0 left-0 right-0 z-[60] bg-blue-600 text-white py-2 px-4" data-testid="impersonation-banner">
          <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
            <div className="flex items-center gap-2 text-sm">
              <Shield size={16} />
              <span className="font-medium">
                Administrando: <strong>{admin?.gym_name || 'Gimnasio'}</strong>
              </span>
            </div>
            <button
              onClick={handleExitImpersonation}
              className="flex items-center gap-2 bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg text-sm font-medium transition-colors"
              data-testid="exit-impersonation-btn"
            >
              <ChevronLeft size={14} />
              Volver a Super Admin
            </button>
          </div>
        </div>
      )}

      {/* Mobile header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-40 border-b px-4 py-3"
        style={{ top: isImpersonating ? '36px' : '0', background: 'var(--sidebar-bg)', borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center justify-between">
          <button onClick={() => setSidebarOpen(true)} className="p-2" style={{ color: 'var(--text-secondary)' }} data-testid="mobile-menu-btn">
            <Menu size={24} />
          </button>
          <div className="flex items-center gap-2">
            {gymLogoUrl ? (
              <img src={gymLogoUrl} alt={gymData?.name || 'Gym'} className="h-8 max-w-[120px] object-contain" data-testid="admin-mobile-logo" />
            ) : (
              <QrCode size={24} style={{ color: 'var(--gym-primary)' }} />
            )}
            <span className="font-bold">{gymData?.name || 'IngresoQR'}</span>
          </div>
          <div className="w-10" />
        </div>
      </header>

      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/60 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}
        style={{ top: isImpersonating ? '36px' : '0', height: isImpersonating ? 'calc(100vh - 36px)' : '100vh' }}>
        <div className="p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {gymLogoUrl ? (
              <img src={gymLogoUrl} alt={gymData?.name || 'Gym'} className="h-10 max-w-[140px] object-contain" data-testid="admin-sidebar-logo" />
            ) : (
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'var(--gym-primary)' }}>
                <QrCode size={22} className="text-black" />
              </div>
            )}
            <div>
              <h1 className="font-bold text-sm">{gymData?.name || 'IngresoQR'}</h1>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{admin?.role === 'super_admin' && !isImpersonating ? 'Super Admin' : 'Panel Admin'}</p>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)} 
            className="lg:hidden p-1"
            style={{ color: 'var(--text-muted)' }}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 px-3 overflow-y-auto scrollbar-thin">
          <div className="space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors"
                  style={isActive 
                    ? { background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }
                    : { color: 'var(--text-secondary)' }
                  }
                  onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}}
                  onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  {item.label}
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--gym-primary)' }} />
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="p-4 border-t" style={{ borderColor: 'var(--border-primary)' }}>
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold" style={{ background: 'var(--bg-tertiary)' }}>
              {admin?.name?.charAt(0) || 'A'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{admin?.name}</p>
              <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{admin?.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="flex items-center justify-center w-10 h-10 rounded-lg transition-colors"
              style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
              data-testid="theme-toggle-btn"
              title={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 flex-1 px-4 py-2 text-sm hover:text-red-500 hover:bg-red-500/5 rounded-lg transition-colors"
              style={{ color: 'var(--text-muted)' }}
              data-testid="admin-logout-btn"
            >
              <LogOut size={18} />
              Cerrar Sesion
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="admin-content" style={{ paddingTop: isImpersonating ? '36px' : '0' }}>
        <div className="p-6 lg:p-8 pt-20 lg:pt-8 pb-16">
          {children}
        </div>
      </main>
    </div>
  );
};
