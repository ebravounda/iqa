import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, Users, CreditCard, Building2, UserCog, Settings, 
  Calendar, Clock, Bell, Shield, QrCode, Menu, X, ChevronLeft,
  LogOut, Smartphone
} from 'lucide-react';

const getNavItems = (role, isImpersonating) => {
  // When impersonating, show gym_admin menu
  const effectiveRole = isImpersonating ? 'gym_admin' : role;

  const items = [
    { path: '/admin', icon: LayoutDashboard, label: 'Dashboard', roles: ['super_admin', 'gym_admin', 'gym_manager', 'trainer'] },
    { path: '/admin/members', icon: Users, label: 'Socios', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/plans', icon: CreditCard, label: 'Planes', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/classes', icon: Calendar, label: 'Clases', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/schedules', icon: Clock, label: 'Horarios', roles: ['super_admin', 'gym_admin', 'gym_manager', 'trainer'] },
    { path: '/admin/access', icon: Shield, label: 'Accesos', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/staff', icon: UserCog, label: 'Personal', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/devices', icon: Smartphone, label: 'Dispositivos', roles: ['super_admin', 'gym_admin'] },
    { path: '/admin/notifications', icon: Bell, label: 'Notificaciones', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/gyms', icon: Building2, label: 'Gimnasios', roles: ['super_admin'] },
    { path: '/admin/settings', icon: Settings, label: 'Configuración', roles: ['super_admin', 'gym_admin'] },
  ];

  return items.filter(item => item.roles.includes(effectiveRole));
};

export const AdminLayout = ({ children }) => {
  const { admin, logout, isImpersonating, exitImpersonation } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const navItems = getNavItems(admin?.role, isImpersonating);

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const handleExitImpersonation = () => {
    exitImpersonation();
    navigate('/admin/gyms');
  };

  return (
    <div className="min-h-screen bg-[#09090B]">
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
      <header className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-[#0a0a0b] border-b border-zinc-800 px-4 py-3"
        style={{ top: isImpersonating ? '36px' : '0' }}>
        <div className="flex items-center justify-between">
          <button onClick={() => setSidebarOpen(true)} className="p-2 text-zinc-400" data-testid="mobile-menu-btn">
            <Menu size={24} />
          </button>
          <div className="flex items-center gap-2">
            <QrCode size={24} style={{ color: 'var(--gym-primary)' }} />
            <span className="font-bold">GymAccess</span>
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
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'var(--gym-primary)' }}>
              <QrCode size={22} className="text-black" />
            </div>
            <div>
              <h1 className="font-bold text-sm">GymAccess</h1>
              <p className="text-xs text-zinc-500">{admin?.role === 'super_admin' && !isImpersonating ? 'Super Admin' : 'Panel Admin'}</p>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)} 
            className="lg:hidden p-1 text-zinc-500"
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
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-zinc-800 text-white' 
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                  }`}
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

        <div className="p-4 border-t border-zinc-800">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-9 h-9 rounded-full bg-zinc-800 flex items-center justify-center text-sm font-bold">
              {admin?.name?.charAt(0) || 'A'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{admin?.name}</p>
              <p className="text-xs text-zinc-500 truncate">{admin?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-4 py-2 text-sm text-zinc-500 hover:text-red-500 hover:bg-red-500/5 rounded-lg transition-colors"
            data-testid="admin-logout-btn"
          >
            <LogOut size={18} />
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="admin-content" style={{ paddingTop: isImpersonating ? '36px' : '0' }}>
        <div className="p-6 lg:p-8 pt-20 lg:pt-8">
          {children}
        </div>
      </main>
    </div>
  );
};
