import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';
import { Trophy, Flame, Star, Crown, Shield, Zap, Calendar, Target, Award, Medal, Search } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BADGE_ICONS = {
  star: Star, fire: Flame, trophy: Trophy, crown: Crown, shield: Shield,
  zap: Zap, flame: Flame, sword: Target, 'calendar-check': Calendar, sunrise: Star,
};

export default function AdminGamification() {
  const { admin, isSuperAdmin } = useAuth();
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchRanking = useCallback(async () => {
    try {
      const params = isSuperAdmin && admin?.gym_id ? `?gym_id=${admin.gym_id}` : '';
      const res = await axios.get(`${API}/gamification/ranking${params}`);
      setRanking(res.data.ranking || []);
    } catch { toast.error('Error al cargar ranking'); }
    finally { setLoading(false); }
  }, [admin, isSuperAdmin]);

  useEffect(() => { fetchRanking(); }, [fetchRanking]);

  const filtered = ranking.filter(r => !search || r.name.toLowerCase().includes(search.toLowerCase()) || r.code.includes(search.toUpperCase()));
  const podium = filtered.slice(0, 3);
  const rest = filtered.slice(3);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6" data-testid="admin-gamification-page">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Trophy size={24} style={{ color: 'var(--gym-primary)' }} /> Ranking y Gamificacion</h1>
        <p className="text-zinc-400 text-sm">Rachas de asistencia, badges y puntuacion de socios</p>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <Input placeholder="Buscar socio..." value={search} onChange={e => setSearch(e.target.value)} className="pl-9 bg-zinc-900 border-zinc-700 text-white" data-testid="search-ranking" />
      </div>

      {/* Podium */}
      {podium.length > 0 && (
        <div className="flex justify-center items-end gap-4 py-6">
          {podium.length > 1 && <PodiumCard member={podium[1]} position={2} />}
          <PodiumCard member={podium[0]} position={1} />
          {podium.length > 2 && <PodiumCard member={podium[2]} position={3} />}
        </div>
      )}

      {/* Rest of ranking */}
      {rest.length > 0 && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400">
                <th className="p-3 text-left font-medium w-12">#</th>
                <th className="p-3 text-left font-medium">Socio</th>
                <th className="p-3 text-center font-medium">Puntos</th>
                <th className="p-3 text-center font-medium hidden sm:table-cell">Racha</th>
                <th className="p-3 text-center font-medium hidden md:table-cell">Visitas</th>
                <th className="p-3 text-center font-medium">Badges</th>
              </tr>
            </thead>
            <tbody>
              {rest.map(m => (
                <tr key={m.member_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                  <td className="p-3 text-zinc-500 font-mono">{m.rank}</td>
                  <td className="p-3">
                    <p className="font-medium text-zinc-200">{m.name}</p>
                    <p className="text-xs text-zinc-500">{m.code}</p>
                  </td>
                  <td className="p-3 text-center font-bold" style={{ color: 'var(--gym-primary)' }}>{m.points}</td>
                  <td className="p-3 text-center hidden sm:table-cell">
                    <span className="flex items-center justify-center gap-1 text-orange-400">
                      <Flame size={14} /> {m.current_streak}d
                    </span>
                  </td>
                  <td className="p-3 text-center text-zinc-300 hidden md:table-cell">{m.total_visits}</td>
                  <td className="p-3 text-center">
                    <div className="flex justify-center gap-0.5">
                      {m.earned_badges.slice(0, 5).map(b => {
                        const Icon = BADGE_ICONS[BADGE_DEFS[b]?.icon] || Award;
                        return <Icon key={b} size={14} className="text-amber-400" />;
                      })}
                      {m.badges_count > 5 && <span className="text-xs text-zinc-500">+{m.badges_count - 5}</span>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {ranking.length === 0 && (
        <div className="text-center py-12 text-zinc-500">
          <Trophy size={48} className="mx-auto mb-4" />
          <p>No hay datos de asistencia para mostrar ranking</p>
        </div>
      )}
    </div>
  );
}

const BADGE_DEFS = {
  first_visit: { icon: 'star' }, regular_10: { icon: 'fire' }, committed_25: { icon: 'trophy' },
  warrior_50: { icon: 'sword' }, legend_100: { icon: 'crown' }, streak_3: { icon: 'flame' },
  streak_7: { icon: 'calendar-check' }, streak_14: { icon: 'zap' }, streak_30: { icon: 'shield' },
  early_bird: { icon: 'sunrise' },
};

function PodiumCard({ member, position }) {
  const sizes = { 1: 'h-32', 2: 'h-24', 3: 'h-20' };
  const colors = { 1: 'from-yellow-500/20 to-yellow-600/5 border-yellow-500/30', 2: 'from-zinc-400/20 to-zinc-500/5 border-zinc-400/30', 3: 'from-amber-700/20 to-amber-800/5 border-amber-700/30' };
  const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };

  return (
    <div className={`flex flex-col items-center ${position === 1 ? 'order-2' : position === 2 ? 'order-1' : 'order-3'}`}>
      <div className={`w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-xl mb-2 border-2 ${position === 1 ? 'border-yellow-500 w-16 h-16' : position === 2 ? 'border-zinc-400' : 'border-amber-700'}`}>
        {member.avatar_url ? <img src={member.avatar_url} alt="" className="w-full h-full rounded-full object-cover" /> : <span>{member.name?.charAt(0)}</span>}
      </div>
      <p className="text-sm font-bold text-zinc-200 text-center max-w-[100px] truncate">{member.name}</p>
      <p className="text-xs font-bold mb-2" style={{ color: 'var(--gym-primary)' }}>{member.points} pts</p>
      <div className={`${sizes[position]} w-20 bg-gradient-to-t ${colors[position]} border rounded-t-lg flex items-center justify-center`}>
        <span className="text-2xl">{medals[position]}</span>
      </div>
    </div>
  );
}
