import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, ShoppingCart, Shield, DollarSign } from 'lucide-react';

/**
 * Bottom nav for admin on mobile. Shows the 5 most-used sections for one-tap access.
 * Hidden on >= lg (desktop keeps the sidebar).
 */
export default function AdminMobileBottomNav({ role, isImpersonating, labels = {} }) {
  const location = useLocation();
  const effectiveRole = isImpersonating ? 'gym_admin' : role;

  const items = [
    { path: '/admin', icon: LayoutDashboard, label: 'Inicio', roles: ['super_admin', 'gym_admin', 'gym_manager', 'trainer'] },
    { path: '/admin/members', icon: Users, label: labels.members || 'Socios', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/pos', icon: ShoppingCart, label: 'TPV', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/access', icon: Shield, label: 'Accesos', roles: ['super_admin', 'gym_admin', 'gym_manager'] },
    { path: '/admin/accounting', icon: DollarSign, label: 'Caja', roles: ['super_admin', 'gym_admin'] },
  ].filter(i => i.roles.includes(effectiveRole));

  if (items.length === 0) return null;

  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-40 border-t"
      style={{
        background: 'var(--sidebar-bg, #09090b)',
        borderColor: 'var(--border-primary, #27272a)',
        paddingBottom: 'env(safe-area-inset-bottom, 0)',
      }}
      data-testid="admin-mobile-bottom-nav"
    >
      <div className="flex items-stretch justify-around">
        {items.map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex-1 flex flex-col items-center justify-center py-2 px-1 text-[11px] font-semibold transition-colors"
              style={{
                color: active ? 'var(--gym-primary, #c5f82a)' : 'var(--text-muted, #71717a)',
              }}
              data-testid={`mobile-nav-${item.label.toLowerCase()}`}
            >
              <Icon size={22} strokeWidth={active ? 2.6 : 2} />
              <span className="mt-0.5">{item.label}</span>
              {active && (
                <span
                  className="absolute top-0 w-10 h-0.5 rounded-b"
                  style={{ background: 'var(--gym-primary, #c5f82a)' }}
                />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
