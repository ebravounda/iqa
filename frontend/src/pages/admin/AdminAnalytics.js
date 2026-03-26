import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getAnalyticsOverview, getHourlyHeatmap, getRevenueComparison, getMemberRetention, getPeakHours, getGyms } from '../../lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';
import { toast } from 'sonner';
import { TrendingUp, Users, Clock, Activity } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

export default function AdminAnalytics() {
  const { admin, isSuperAdmin } = useAuth();
  const [selectedGym, setSelectedGym] = useState(admin?.gym_id || '');
  const [gyms, setGyms] = useState([]);
  const [overview, setOverview] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [revenue, setRevenue] = useState([]);
  const [retention, setRetention] = useState([]);
  const [peakHours, setPeakHours] = useState(null);

  useEffect(() => {
    if (isSuperAdmin) {
      getGyms().then(res => {
        setGyms(res.data);
        if (res.data.length > 0 && !selectedGym) setSelectedGym(res.data[0].id);
      }).catch(() => {});
    }
  }, [isSuperAdmin]);

  const gymId = isSuperAdmin ? selectedGym : admin?.gym_id;

  const load = useCallback(async () => {
    if (!gymId) return;
    try {
      const [ov, hm, rv, rt, ph] = await Promise.all([
        getAnalyticsOverview(gymId),
        getHourlyHeatmap(gymId),
        getRevenueComparison(gymId),
        getMemberRetention(gymId),
        getPeakHours(gymId),
      ]);
      setOverview(ov.data);
      setHeatmap(hm.data);
      setRevenue(rv.data);
      setRetention(rt.data);
      setPeakHours(ph.data);
    } catch (e) { 
      console.error('Analytics Error:', e?.response?.status, e?.response?.data, e?.message);
      toast.error(`Error Analytics: ${e?.response?.data?.detail || e?.message || 'Error de conexion'}`); 
    }
  }, [gymId]);

  useEffect(() => { if (gymId) load(); }, [load, gymId]);

  if (!gymId && isSuperAdmin) return (
    <div className="space-y-6" data-testid="analytics-page">
      <div><h1 className="text-2xl font-black text-white">Analytics</h1></div>
      <div className="max-w-sm">
        <label className="text-sm text-zinc-400 mb-1 block">Seleccionar Gimnasio</label>
        <Select value={selectedGym} onValueChange={setSelectedGym}>
          <SelectTrigger className="bg-zinc-900 border-zinc-700" data-testid="analytics-gym-select">
            <SelectValue placeholder="Seleccionar gimnasio" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-700">
            {gyms.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <p className="text-zinc-500">Selecciona un gimnasio para ver sus analytics.</p>
    </div>
  );

  if (!overview) return <div className="p-6 text-zinc-400">Cargando analytics...</div>;

  const maxHeat = Math.max(...heatmap.map(h => h.count), 1);
  const getHeatColor = (count) => {
    const intensity = count / maxHeat;
    if (intensity === 0) return 'bg-zinc-800';
    if (intensity < 0.25) return 'bg-emerald-900/40';
    if (intensity < 0.5) return 'bg-emerald-700/50';
    if (intensity < 0.75) return 'bg-emerald-500/60';
    return 'bg-emerald-400/80';
  };

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const days = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'];

  return (
    <div className="space-y-6" data-testid="analytics-page">
      <div className="flex flex-col sm:flex-row sm:items-end gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">Analytics</h1>
          <p className="text-zinc-400 text-sm">Retencion, horas pico y comparativa de ingresos</p>
        </div>
        {isSuperAdmin && (
          <div className="sm:ml-auto min-w-[200px]">
            <Select value={selectedGym} onValueChange={setSelectedGym}>
              <SelectTrigger className="bg-zinc-900 border-zinc-700" data-testid="analytics-gym-select">
                <SelectValue placeholder="Gimnasio" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {gyms.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1"><Users size={14} className="text-zinc-400" /><p className="text-xs text-zinc-400">Socios activos</p></div>
          <p className="text-2xl font-black text-white">{overview.active_members}</p>
          <p className="text-xs text-zinc-500">de {overview.total_members} totales</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1"><TrendingUp size={14} className="text-zinc-400" /><p className="text-xs text-zinc-400">Tasa de retencion</p></div>
          <p className="text-2xl font-black text-[var(--gym-primary)]">{overview.retention_rate}%</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1"><Activity size={14} className="text-zinc-400" /><p className="text-xs text-zinc-400">Nuevos este mes</p></div>
          <p className="text-2xl font-black text-white">{overview.new_this_month}</p>
          <p className={`text-xs ${overview.member_growth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {overview.member_growth >= 0 ? '+' : ''}{overview.member_growth} vs mes anterior
          </p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1"><Clock size={14} className="text-zinc-400" /><p className="text-xs text-zinc-400">Hora pico</p></div>
          <p className="text-2xl font-black text-white">{peakHours?.peak_hour?.hour || '-'}</p>
          <p className="text-xs text-zinc-500">{peakHours?.peak_hour?.entries || 0} entradas (30d)</p>
        </div>
      </div>

      {/* Revenue Comparison */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h3 className="font-bold text-white mb-4">Comparativa Mensual de Ingresos</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={revenue}>
            <XAxis dataKey="month" tick={{ fill: '#71717A', fontSize: 12 }} />
            <YAxis tick={{ fill: '#71717A', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#18181B', border: '1px solid #27272A', borderRadius: 8, color: '#fff' }} />
            <Legend />
            <Bar dataKey="membresias" name="Membresias" fill="#E1FF01" radius={[4, 4, 0, 0]} />
            <Bar dataKey="pos" name="Ventas POS" fill="#3B82F6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Retention Chart */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h3 className="font-bold text-white mb-4">Retencion de Socios</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={retention}>
            <XAxis dataKey="month" tick={{ fill: '#71717A', fontSize: 12 }} />
            <YAxis tick={{ fill: '#71717A', fontSize: 11 }} domain={[0, 100]} />
            <Tooltip contentStyle={{ background: '#18181B', border: '1px solid #27272A', borderRadius: 8, color: '#fff' }} />
            <Legend />
            <Line type="monotone" dataKey="retention" name="Retencion %" stroke="#E1FF01" strokeWidth={2} dot={{ fill: '#E1FF01' }} />
            <Line type="monotone" dataKey="new" name="Nuevos" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Peak Hours Heatmap */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h3 className="font-bold text-white mb-4">Horas Pico de Acceso (ultimos 30 dias)</h3>
        <div className="overflow-x-auto">
          <div className="inline-block min-w-[600px]">
            <div className="grid gap-px" style={{ gridTemplateColumns: `60px repeat(24, 1fr)` }}>
              <div />
              {hours.map(h => <div key={h} className="text-center text-[10px] text-zinc-500 py-1">{h}</div>)}
              {days.map((day, d) => (
                <React.Fragment key={`day-${d}`}>
                  <div className="text-xs text-zinc-400 flex items-center pr-2">{day}</div>
                  {hours.map(h => {
                    const cell = heatmap.find(c => c.day === d && c.hour === h);
                    return (
                      <div
                        key={`${d}-${h}`}
                        className={`aspect-square rounded-sm ${getHeatColor(cell?.count || 0)} cursor-default`}
                        title={`${day} ${h}:00 - ${cell?.count || 0} accesos`}
                      />
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-3 justify-end">
              <span className="text-[10px] text-zinc-500">Menos</span>
              {['bg-zinc-800', 'bg-emerald-900/40', 'bg-emerald-700/50', 'bg-emerald-500/60', 'bg-emerald-400/80'].map((c, i) => (
                <div key={i} className={`w-3 h-3 rounded-sm ${c}`} />
              ))}
              <span className="text-[10px] text-zinc-500">Mas</span>
            </div>
          </div>
        </div>
      </div>

      {/* Peak Hours Bar */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h3 className="font-bold text-white mb-4">Distribucion Horaria de Entradas</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={peakHours?.hourly || []}>
            <XAxis dataKey="hour" tick={{ fill: '#71717A', fontSize: 10 }} interval={1} />
            <YAxis tick={{ fill: '#71717A', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#18181B', border: '1px solid #27272A', borderRadius: 8, color: '#fff' }} />
            <Bar dataKey="avg" name="Promedio diario" fill="#E1FF01" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
