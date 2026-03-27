import { useState, useEffect, useCallback } from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';
import { ShieldAlert, ShieldCheck, ShieldX, Unlock, Trash2, RefreshCw, Search, Filter } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminSecurity() {
  const { admin } = useAuth();
  const [stats, setStats] = useState(null);
  const [blockedIps, setBlockedIps] = useState({ active: [], expired: [] });
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('blocked');
  const [filterType, setFilterType] = useState('all');
  const [filterSuccess, setFilterSuccess] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchData = useCallback(async () => {
    if (admin?.role !== 'super_admin') return;
    setLoading(true);
    try {
      const [statsRes, blockedRes, attemptsRes] = await Promise.all([
        axios.get(`${API}/security/stats`),
        axios.get(`${API}/security/blocked-ips`),
        axios.get(`${API}/security/login-attempts?limit=200`)
      ]);
      setStats(statsRes.data);
      setBlockedIps(blockedRes.data);
      setAttempts(attemptsRes.data.attempts);
    } catch (err) {
      toast.error('Error al cargar datos de seguridad');
    } finally {
      setLoading(false);
    }
  }, [admin]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (admin?.role !== 'super_admin') return <Navigate to="/admin" replace />;

  const handleUnblock = async (ip) => {
    try {
      await axios.delete(`${API}/security/blocked-ips/${encodeURIComponent(ip)}`);
      toast.success(`IP ${ip} desbloqueada`);
      fetchData();
    } catch { toast.error('Error al desbloquear IP'); }
  };

  const handleUnblockAll = async () => {
    if (!window.confirm('Desbloquear TODAS las IPs?')) return;
    try {
      await axios.delete(`${API}/security/blocked-ips`);
      toast.success('Todas las IPs desbloqueadas');
      fetchData();
    } catch { toast.error('Error'); }
  };

  const formatDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleString('es-ES', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  const filteredAttempts = attempts.filter(a => {
    if (filterType !== 'all' && a.type !== filterType) return false;
    if (filterSuccess === 'failed' && a.success) return false;
    if (filterSuccess === 'success' && !a.success) return false;
    if (searchTerm && !a.ip?.includes(searchTerm) && !a.identifier?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-security-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Seguridad</h1>
          <p className="text-zinc-400 text-sm">Monitoreo de accesos e IPs bloqueadas</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm" className="border-zinc-700 text-zinc-300" data-testid="security-refresh-btn">
          <RefreshCw size={16} className="mr-2" /> Actualizar
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard icon={ShieldX} label="IPs Bloqueadas" value={stats.active_blocks} color="text-red-500" bg="bg-red-500/10" testId="stat-active-blocks" />
          <StatCard icon={ShieldAlert} label="Fallos 24h" value={stats.failed_24h} color="text-amber-500" bg="bg-amber-500/10" testId="stat-fails-24h" />
          <StatCard icon={ShieldAlert} label="Fallos 7 dias" value={stats.failed_7d} color="text-orange-500" bg="bg-orange-500/10" testId="stat-fails-7d" />
          <StatCard icon={ShieldCheck} label="Exitosos 24h" value={stats.success_24h} color="text-emerald-500" bg="bg-emerald-500/10" testId="stat-success-24h" />
          <StatCard icon={ShieldX} label="Bloqueos total" value={stats.total_blocks_history} color="text-zinc-400" bg="bg-zinc-800" testId="stat-total-blocks" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800 pb-1">
        <button
          onClick={() => setTab('blocked')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${tab === 'blocked' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
          data-testid="tab-blocked-ips"
        >
          IPs Bloqueadas ({blockedIps.active.length})
        </button>
        <button
          onClick={() => setTab('attempts')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${tab === 'attempts' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
          data-testid="tab-login-attempts"
        >
          Intentos de Acceso ({attempts.length})
        </button>
      </div>

      {/* Tab: Blocked IPs */}
      {tab === 'blocked' && (
        <div className="space-y-4">
          {blockedIps.active.length > 0 && (
            <div className="flex justify-end">
              <Button onClick={handleUnblockAll} variant="outline" size="sm" className="border-red-800 text-red-400 hover:bg-red-500/10" data-testid="unblock-all-btn">
                <Trash2 size={14} className="mr-2" /> Desbloquear todas
              </Button>
            </div>
          )}

          {blockedIps.active.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <ShieldCheck size={48} className="mx-auto mb-4 text-emerald-500" />
              <p className="text-lg font-medium text-zinc-300">Sin IPs bloqueadas</p>
              <p className="text-sm">No hay amenazas activas detectadas</p>
            </div>
          ) : (
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="text-left p-3 font-medium">IP</th>
                    <th className="text-left p-3 font-medium hidden sm:table-cell">Razon</th>
                    <th className="text-left p-3 font-medium hidden md:table-cell">Ultimo intento</th>
                    <th className="text-left p-3 font-medium">Bloqueada hasta</th>
                    <th className="text-left p-3 font-medium">Tipo</th>
                    <th className="p-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {blockedIps.active.map((b, i) => (
                    <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30" data-testid={`blocked-ip-row-${i}`}>
                      <td className="p-3 font-mono text-red-400">{b.ip}</td>
                      <td className="p-3 text-zinc-400 hidden sm:table-cell">{b.reason}</td>
                      <td className="p-3 text-zinc-400 hidden md:table-cell">{b.last_identifier || '-'}</td>
                      <td className="p-3 text-zinc-300">{formatDate(b.blocked_until)}</td>
                      <td className="p-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${b.type === 'admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                          {b.type === 'admin' ? 'Admin' : 'Socio'}
                        </span>
                      </td>
                      <td className="p-3">
                        <Button onClick={() => handleUnblock(b.ip)} variant="ghost" size="sm" className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10" data-testid={`unblock-ip-${i}`}>
                          <Unlock size={14} />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Expired blocks history */}
          {blockedIps.expired.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Historial de bloqueos expirados</h3>
              <div className="bg-zinc-900/30 border border-zinc-800/50 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800/50 text-zinc-500">
                      <th className="text-left p-3 font-medium">IP</th>
                      <th className="text-left p-3 font-medium hidden sm:table-cell">Razon</th>
                      <th className="text-left p-3 font-medium">Fecha bloqueo</th>
                      <th className="text-left p-3 font-medium">Tipo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {blockedIps.expired.map((b, i) => (
                      <tr key={i} className="border-b border-zinc-800/30 text-zinc-500">
                        <td className="p-3 font-mono">{b.ip}</td>
                        <td className="p-3 hidden sm:table-cell">{b.reason}</td>
                        <td className="p-3">{formatDate(b.blocked_at)}</td>
                        <td className="p-3">
                          <span className={`text-xs px-2 py-1 rounded-full ${b.type === 'admin' ? 'bg-purple-500/10 text-purple-500' : 'bg-blue-500/10 text-blue-500'}`}>
                            {b.type === 'admin' ? 'Admin' : 'Socio'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Login Attempts */}
      {tab === 'attempts' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <Input
                placeholder="Buscar por IP o email/codigo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 bg-zinc-900 border-zinc-700 text-white"
                data-testid="search-attempts-input"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-zinc-500" />
              <select value={filterType} onChange={e => setFilterType(e.target.value)}
                className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2"
                data-testid="filter-type-select"
              >
                <option value="all">Todos</option>
                <option value="admin">Admin</option>
                <option value="member">Socio</option>
              </select>
              <select value={filterSuccess} onChange={e => setFilterSuccess(e.target.value)}
                className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2"
                data-testid="filter-success-select"
              >
                <option value="all">Todos</option>
                <option value="failed">Fallidos</option>
                <option value="success">Exitosos</option>
              </select>
            </div>
          </div>

          {filteredAttempts.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <ShieldCheck size={48} className="mx-auto mb-4 text-zinc-600" />
              <p>No hay intentos de acceso registrados</p>
            </div>
          ) : (
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400">
                      <th className="text-left p-3 font-medium">Estado</th>
                      <th className="text-left p-3 font-medium">IP</th>
                      <th className="text-left p-3 font-medium">Email / Codigo</th>
                      <th className="text-left p-3 font-medium">Tipo</th>
                      <th className="text-left p-3 font-medium">Fecha</th>
                      <th className="text-left p-3 font-medium hidden lg:table-cell">User Agent</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAttempts.map((a, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30" data-testid={`attempt-row-${i}`}>
                        <td className="p-3">
                          {a.success ? (
                            <span className="flex items-center gap-1 text-emerald-400"><ShieldCheck size={14} /> OK</span>
                          ) : (
                            <span className="flex items-center gap-1 text-red-400"><ShieldX size={14} /> Fallo</span>
                          )}
                        </td>
                        <td className="p-3 font-mono text-xs text-zinc-300">{a.ip}</td>
                        <td className="p-3 text-zinc-300">{a.identifier}</td>
                        <td className="p-3">
                          <span className={`text-xs px-2 py-1 rounded-full ${a.type === 'admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                            {a.type === 'admin' ? 'Admin' : 'Socio'}
                          </span>
                        </td>
                        <td className="p-3 text-zinc-400">{formatDate(a.timestamp)}</td>
                        <td className="p-3 text-zinc-500 text-xs max-w-[200px] truncate hidden lg:table-cell">{a.user_agent || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color, bg, testId }) {
  return (
    <div className={`${bg} border border-zinc-800 rounded-xl p-4`} data-testid={testId}>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={18} className={color} />
        <span className="text-xs text-zinc-400">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
