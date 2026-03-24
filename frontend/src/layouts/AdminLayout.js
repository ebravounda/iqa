import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, Users, CreditCard, History, 
  Settings, LogOut, Menu, X, Building2, Cpu, FileText
} from 'lucide-react';

const navItems = [
  { path: '/admin', icon: LayoutDashboard, label: 'Dashboard', roles: ['super_admin', 'gym_admin'] },
  { path: '/admin/gyms', icon: Building2, label: 'Gimnasios', roles: ['super_admin'] },
  { path: '/admin/members', icon: Users, label: 'Socios', roles: ['super_admin', 'gym_admin'] },
  { path: '/admin/plans', icon: CreditCard, label: 'Planes', roles: ['super_admin', 'gym_admin'] },
  { path: '/admin/access', icon: History, label: 'Accesos', roles: ['super_admin', 'gym_admin'] },
  { path: '/admin/devices', icon: Cpu, label: 'Dispositivos', roles: ['super_admin', 'gym_admin'] },
  { path: '/admin/templates', icon: FileText, label: 'Plantillas Email', roles: ['super_admin', 'gym_admin'] },
  { path: '/admin/settings', icon: Settings, label: 'Configuración', roles: ['super_admin', 'gym_admin'] },
];

export const AdminLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { admin, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const filteredNavItems = navItems.filter(item => 
    item.roles.includes(admin?.role)
  );

  return (
    <div className="min-h-screen bg-[#09090B]">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-[#0a0a0b] border-b border-zinc-800 z-50 flex items-center px-4">
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-zinc-800 rounded-lg"
          data-testid="mobile-menu-toggle"
        >
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
        <span className="ml-4 font-bold text-lg">GymAccess</span>
      </div>

      {/* Sidebar */}
      <aside className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="p-6 border-b border-zinc-800">
          <h1 className="text-xl font-black tracking-tight">
            <span style={{ color: 'var(--gym-primary)' }}>GYM</span>ACCESS
          </h1>
          <p className="text-xs text-zinc-500 mt-1">Panel de Administración</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {filteredNavItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-zinc-800 text-white' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                }`}
                data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-zinc-800">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-bold">
              {admin?.name?.charAt(0) || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{admin?.name}</p>
              <p className="text-xs text-zinc-500 truncate">{admin?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-zinc-400 hover:text-red-400 hover:bg-zinc-800/50 transition-colors"
            data-testid="logout-btn"
          >
            <LogOut size={20} />
            <span className="font-medium">Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="admin-content">
        <div className="p-6 lg:p-8 pt-20 lg:pt-8">
          {children}
        </div>
      </main>
    </div>
  );
};
