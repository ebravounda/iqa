import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useBusiness } from '../../context/BusinessContext';
import { getDashboardStats, getAccessLogs, getExpiringMemberships, getDailyAccessStats } from '../../lib/api';
import { formatDateTime, formatCurrency } from '../../lib/utils';
import { 
  Users, TrendingUp, Calendar, DollarSign, 
  ArrowUpRight, Clock, AlertTriangle, Activity, LogIn, LogOut
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminDashboard() {
  const { admin, isSuperAdmin } = useAuth();
  const { labels } = useBusiness();
  const [stats, setStats] = useState(null);
  const [recentAccess, setRecentAccess] = useState([]);
  const [expiringMemberships, setExpiringMemberships] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, accessRes, expiringRes, dailyRes] = await Promise.all([
        getDashboardStats(),
        getAccessLogs(null, null, null, null, 10),
        getExpiringMemberships(10),
        getDailyAccessStats(null, 7)
      ]);
      setStats(statsRes.data);
      setRecentAccess(accessRes.data);
      setExpiringMemberships(expiringRes.data);
      setChartData(dailyRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

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
        <div className="stat-card" data-testid="stat-active-members">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">{labels.members} Activos</span>
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

        <div className="stat-card" data-testid="stat-today-accesses">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">{labels.accesses} Hoy</span>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <TrendingUp size={20} className="text-blue-500" />
            </div>
          </div>
          <p className="text-3xl font-black">{stats?.today_accesses || 0}</p>
          <p className="text-xs text-zinc-500 mt-1">
            {stats?.week_accesses || 0} esta semana
          </p>
        </div>

        <div className="stat-card" data-testid="stat-active-memberships">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">{labels.memberships} Activas</span>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
              <Calendar size={20} className="text-purple-500" />
            </div>
          </div>
          <p className="text-3xl font-black">{stats?.active_memberships || 0}</p>
          <p className="text-xs text-zinc-500 mt-1">
            {expiringMemberships.length} por vencer
          </p>
        </div>

        <div className="stat-card" data-testid="stat-revenue">
          <div className="flex items-center justify-between mb-4">
            <span className="text-zinc-400 text-sm font-medium">Ingresos del Mes</span>
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'rgba(225, 255, 1, 0.1)' }}>
              <DollarSign size={20} style={{ color: 'var(--gym-primary)' }} />
            </div>
          </div>
          <p className="text-3xl font-black">{formatCurrency(stats?.month_revenue || 0)}</p>
          {isSuperAdmin && (
            <p className="text-xs text-zinc-500 mt-1">
              {stats?.gyms_count || 0} negocios
            </p>
          )}
        </div>
      </div>

      {/* Real-time Occupancy Widget */}
      {stats?.occupancy && (
        <div className="stat-card relative overflow-hidden" data-testid="occupancy-widget">
          <div className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-5" style={{ background: 'var(--gym-primary)', filter: 'blur(40px)' }} />
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center relative" style={{ backgroundColor: 'rgba(225, 255, 1, 0.1)' }}>
                <Activity size={24} style={{ color: 'var(--gym-primary)' }} />
                <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <div>
                <h3 className="font-bold text-lg">Ocupación en Tiempo Real</h3>
                <p className="text-zinc-500 text-xs">Personas dentro ahora mismo</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-5xl font-black" style={{ color: 'var(--gym-primary)' }} data-testid="occupancy-count">
                {stats.occupancy.current}
              </p>
              {stats.occupancy.max_capacity && (
                <p className="text-xs text-zinc-500">de {stats.occupancy.max_capacity} máx.</p>
              )}
            </div>
          </div>
          {stats.occupancy.max_capacity && stats.occupancy.occupancy_percent !== null && (
            <div className="mb-4">
              <div className="w-full bg-zinc-800 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ${
                    stats.occupancy.occupancy_percent >= 90 ? 'bg-red-500' :
                    stats.occupancy.occupancy_percent >= 70 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.min(stats.occupancy.occupancy_percent, 100)}%` }}
                />
              </div>
              <p className={`text-xs mt-1 font-bold ${
                stats.occupancy.occupancy_percent >= 90 ? 'text-red-400' :
                stats.occupancy.occupancy_percent >= 70 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {stats.occupancy.occupancy_percent}% de capacidad
              </p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
              <LogIn size={18} className="text-emerald-400" />
              <div>
                <p className="text-lg font-black text-emerald-400" data-testid="entries-today">{stats.occupancy.entries_today}</p>
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Entradas hoy</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-xl bg-blue-500/5 border border-blue-500/10">
              <LogOut size={18} className="text-blue-400" />
              <div>
                <p className="text-lg font-black text-blue-400" data-testid="exits-today">{stats.occupancy.exits_today}</p>
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Salidas hoy</p>
              </div>
            </div>
          </div>
          <p className="text-[10px] text-zinc-600 mt-3 text-right">Se actualiza cada 30 segundos</p>
        </div>
      )}

      {/* Suspended Members Alert */}
      {stats?.suspended_members > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 flex items-center gap-3" data-testid="suspended-alert">
          <AlertTriangle size={20} className="text-amber-500 shrink-0" />
          <p className="text-sm text-amber-400">
            <span className="font-bold">{stats.suspended_members}</span> {labels.members.toLowerCase()} suspendidos
          </p>
        </div>
      )}

      {/* Capacity Bar */}
      {stats?.capacity && (
        <div className="stat-card" data-testid="capacity-bar">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-bold text-lg">{labels.memberCapacity}</h3>
              <p className="text-zinc-400 text-sm">
                {stats.capacity.active_members} de {stats.capacity.max_members} {labels.members.toLowerCase()}
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
        {/* Chart - Real Data */}
        <div className="lg:col-span-2 chart-container" data-testid="access-chart">
          <h3 className="font-bold mb-6">{labels.accesses} de la Semana</h3>
          <ResponsiveContainer width="100%" height={250}>
            {chartData.length > 0 ? (
              <BarChart data={chartData}>
                <XAxis 
                  dataKey="day_name" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: '#71717A', fontSize: 12 }}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: '#71717A', fontSize: 12 }}
                  allowDecimals={false}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#18181B', 
                    border: '1px solid #27272A',
                    borderRadius: '8px'
                  }}
                  formatter={(value, name) => [value, name === 'entradas' ? 'Entradas' : 'Total Accesos']}
                />
                <Bar dataKey="entradas" fill="var(--gym-primary)" radius={[4, 4, 0, 0]} name="Entradas" />
                <Bar dataKey="accesos" fill="#3B82F6" radius={[4, 4, 0, 0]} opacity={0.4} name="Total" />
              </BarChart>
            ) : (
              <AreaChart data={[{ day_name: '-', accesos: 0 }]}>
                <XAxis dataKey="day_name" />
                <Area type="monotone" dataKey="accesos" />
              </AreaChart>
            )}
          </ResponsiveContainer>
          {chartData.length === 0 && (
            <p className="text-center text-zinc-500 text-sm mt-2">Sin datos de acceso esta semana</p>
          )}
        </div>

        {/* Expiring Memberships */}
        <div className="stat-card" data-testid="expiring-memberships">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={18} className="text-amber-500" />
            <h3 className="font-bold">Por Vencer</h3>
          </div>
          <div className="space-y-3">
            {expiringMemberships.length === 0 ? (
              <p className="text-zinc-500 text-sm">No hay {labels.memberships.toLowerCase()} por vencer</p>
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
      <div className="stat-card" data-testid="recent-access-table">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Clock size={18} className="text-zinc-400" />
            <h3 className="font-bold">{labels.accesses} Recientes</h3>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>{labels.member}</th>
                <th>Código</th>
                {isSuperAdmin && <th>Gimnasio</th>}
                <th>Dirección</th>
                <th>Fecha/Hora</th>
              </tr>
            </thead>
            <tbody>
              {(isSuperAdmin && stats?.recent_accesses_by_gym?.length > 0 ? stats.recent_accesses_by_gym : recentAccess).length === 0 ? (
                <tr>
                  <td colSpan={isSuperAdmin ? 5 : 4} className="text-center text-zinc-500">
                    No hay accesos registrados
                  </td>
                </tr>
              ) : (
                (isSuperAdmin && stats?.recent_accesses_by_gym?.length > 0 ? stats.recent_accesses_by_gym : recentAccess).map((log) => (
                  <tr key={log.id}>
                    <td className="font-medium">{log.member_name || log.guest_name || '-'}</td>
                    <td>
                      <code className="text-xs bg-zinc-800 px-2 py-1 rounded">
                        {log.member_code || log.guest_code || '-'}
                      </code>
                    </td>
                    {isSuperAdmin && (
                      <td>
                        <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded-full">
                          {log.gym_name || '-'}
                        </span>
                      </td>
                    )}
                    <td>
                      <span className={`badge ${log.direction === 'entrada' ? 'badge-success' : 'badge-primary'}`}>
                        {log.direction === 'entrada' ? 'Entrada' : 'Salida'}
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
