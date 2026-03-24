import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getDashboardStats, getAccessLogs, getExpiringMemberships } from '../../lib/api';
import { formatDateTime, formatCurrency } from '../../lib/utils';
import { 
  Users, TrendingUp, Calendar, DollarSign, 
  ArrowUpRight, ArrowDownRight, Clock, AlertTriangle
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminDashboard() {
  const { admin, isSuperAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentAccess, setRecentAccess] = useState([]);
  const [expiringMemberships, setExpiringMemberships] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, accessRes, expiringRes] = await Promise.all([
        getDashboardStats(),
        getAccessLogs(null, null, null, null, 10),
        getExpiringMemberships(10)
      ]);
      setStats(statsRes.data);
      setRecentAccess(accessRes.data);
      setExpiringMemberships(expiringRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock chart data
  const chartData = [
    { name: 'Lun', accesos: 45 },
    { name: 'Mar', accesos: 52 },
    { name: 'Mie', accesos: 38 },
    { name: 'Jue', accesos: 65 },
    { name: 'Vie', accesos: 78 },
    { name: 'Sab', accesos: 92 },
    { name: 'Dom', accesos: 35 },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-4 w-24 mb-4" />
              <div className="skeleton h-8 w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 stagger-children" data-testid="admin-dashboard">
      <div>
        <h1 className="text-2xl font-black tracking-tight mb-1">Dashboard</h1>
        <p className="text-zinc-400">Bienvenido, {admin?.name}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">Socios Activos</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <Users size={20} className="text-emerald-500" />
            </div>
          </div>
          <p className="text-3xl font-black">{stats?.active_members || 0}</p>
          <p className="text-xs text-zinc-500 mt-1 flex items-center gap-1">
            <ArrowUpRight size={14} className="text-emerald-500" />
            {stats?.pending_members || 0} pendientes
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">Accesos Hoy</span>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <TrendingUp size={20} className="text-blue-500" />
            </div>
          </div>
          <p className="text-3xl font-black">{stats?.today_accesses || 0}</p>
          <p className="text-xs text-zinc-500 mt-1">
            {stats?.week_accesses || 0} esta semana
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">Membresías Activas</span>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
              <Calendar size={20} className="text-purple-500" />
            </div>
          </div>
          <p className="text-3xl font-black">{stats?.active_memberships || 0}</p>
          <p className="text-xs text-zinc-500 mt-1">
            {expiringMemberships.length} por vencer
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">Ingresos del Mes</span>
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'rgba(225, 255, 1, 0.1)' }}>
              <DollarSign size={20} style={{ color: 'var(--gym-primary)' }} />
            </div>
          </div>
          <p className="text-3xl font-black">{formatCurrency(stats?.month_revenue || 0)}</p>
          {isSuperAdmin && (
            <p className="text-xs text-zinc-500 mt-1">
              {stats?.gyms_count || 0} gimnasios
            </p>
          )}
        </div>
      </div>

      {/* Capacity Bar (when gym has max_members set) */}
      {stats?.capacity && (
        <div className="stat-card" data-testid="capacity-bar">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-bold text-lg">Capacidad de Socios</h3>
              <p className="text-zinc-400 text-sm">
                {stats.capacity.active_members} de {stats.capacity.max_members} socios
              </p>
            </div>
            <span className={`text-2xl font-black ${
              stats.capacity.usage_percent >= 90 ? 'text-red-500' : 
              stats.capacity.usage_percent >= 70 ? 'text-amber-500' : 'text-emerald-500'
            }`}>
              {stats.capacity.usage_percent}%
            </span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-4 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                stats.capacity.usage_percent >= 90 ? 'bg-red-500' : 
                stats.capacity.usage_percent >= 70 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(stats.capacity.usage_percent, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-zinc-500">
            <span>0</span>
            <span>{Math.round(stats.capacity.max_members / 2)}</span>
            <span>{stats.capacity.max_members}</span>
          </div>
        </div>
      )}

      {/* Charts and Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2 chart-container">
          <h3 className="font-bold mb-6">Accesos de la Semana</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorAccesos" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--gym-primary)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--gym-primary)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false}
                tick={{ fill: '#71717A', fontSize: 12 }}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false}
                tick={{ fill: '#71717A', fontSize: 12 }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#18181B', 
                  border: '1px solid #27272A',
                  borderRadius: '8px'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="accesos" 
                stroke="var(--gym-primary)" 
                fillOpacity={1} 
                fill="url(#colorAccesos)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Expiring Memberships */}
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={18} className="text-amber-500" />
            <h3 className="font-bold">Por Vencer</h3>
          </div>
          <div className="space-y-3">
            {expiringMemberships.length === 0 ? (
              <p className="text-zinc-500 text-sm">No hay membresías por vencer</p>
            ) : (
              expiringMemberships.slice(0, 5).map((m) => (
                <div key={m.id} className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
                  <div>
                    <p className="font-medium text-sm">{m.member?.name}</p>
                    <p className="text-xs text-zinc-500">{m.member?.code}</p>
                  </div>
                  <span className="badge badge-warning text-xs">
                    {new Date(m.end_date).toLocaleDateString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Access */}
      <div className="stat-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Clock size={18} className="text-zinc-400" />
            <h3 className="font-bold">Accesos Recientes</h3>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Socio</th>
                <th>Código</th>
                <th>Dirección</th>
                <th>Fecha/Hora</th>
              </tr>
            </thead>
            <tbody>
              {recentAccess.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center text-zinc-500">
                    No hay accesos registrados
                  </td>
                </tr>
              ) : (
                recentAccess.map((log) => (
                  <tr key={log.id}>
                    <td className="font-medium">{log.member_name}</td>
                    <td>
                      <code className="text-xs bg-zinc-800 px-2 py-1 rounded">
                        {log.member_code}
                      </code>
                    </td>
                    <td>
                      <span className={`badge ${log.direction === 'entrada' ? 'badge-success' : 'badge-primary'}`}>
                        {log.direction === 'entrada' ? '→ Entrada' : '← Salida'}
                      </span>
                    </td>
                    <td className="text-zinc-400 text-sm">{formatDateTime(log.timestamp)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
