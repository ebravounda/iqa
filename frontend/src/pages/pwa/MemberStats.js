import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getMemberVisitStats } from '../../lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowLeft, TrendingUp, Calendar, Activity, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function MemberStats() {
  const { member } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (member?.id) {
      getMemberVisitStats(member.id)
        .then(res => setStats(res.data))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [member]);

  if (loading) return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-zinc-950 text-white pb-24" data-testid="member-stats-page">
      {/* Header */}
      <div className="bg-zinc-900 border-b border-zinc-800 p-4 flex items-center gap-3">
        <button onClick={() => navigate('/app')} className="p-2 hover:bg-zinc-800 rounded-lg transition-colors">
          <ArrowLeft size={20} />
        </button>
        <h1 className="font-bold text-lg">Mis Estadisticas</h1>
      </div>

      <div className="p-4 space-y-4 max-w-lg mx-auto">
        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
            <TrendingUp size={20} className="mx-auto text-[var(--gym-primary)] mb-2" />
            <p className="text-2xl font-black text-white">{stats?.total_visits || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Total</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
            <Calendar size={20} className="mx-auto text-emerald-400 mb-2" />
            <p className="text-2xl font-black text-white">{stats?.this_month || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Este mes</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
            <Activity size={20} className="mx-auto text-cyan-400 mb-2" />
            <p className="text-2xl font-black text-white">{stats?.this_week || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Semana</p>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h3 className="font-bold text-sm mb-4 flex items-center gap-2">
            <Clock size={16} className="text-[var(--gym-primary)]" />
            Visitas ultimos 6 meses
          </h3>
          {stats?.monthly?.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stats.monthly} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
                <XAxis dataKey="month" tick={{ fill: '#71717a', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8, fontSize: 13 }}
                  labelStyle={{ color: '#a1a1aa' }}
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                />
                <Bar dataKey="visits" fill="var(--gym-primary)" radius={[6, 6, 0, 0]} name="Visitas" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-zinc-500 text-sm text-center py-8">Sin datos de visitas aun</p>
          )}
        </div>

        {/* Motivational */}
        {stats?.this_month > 0 && (
          <div className="bg-gradient-to-r from-[var(--gym-primary)]/10 to-transparent border border-[var(--gym-primary)]/20 rounded-xl p-4">
            <p className="text-sm text-zinc-300">
              {stats.this_month >= 20 ? 'Increible! Eres un atleta dedicado.' :
               stats.this_month >= 12 ? 'Excelente ritmo! Sigue asi.' :
               stats.this_month >= 8 ? 'Buen trabajo! Vas por buen camino.' :
               stats.this_month >= 4 ? 'Cada visita cuenta. Puedes mejorar!' :
               'Animo! Intenta venir mas seguido.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
