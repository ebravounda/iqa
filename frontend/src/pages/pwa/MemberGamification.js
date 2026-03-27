import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Trophy, Flame, Star, Crown, Shield, Zap, Target, Calendar, ArrowLeft, Award, Lock } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BADGE_ICONS = { star: Star, fire: Flame, trophy: Trophy, crown: Crown, shield: Shield, zap: Zap, flame: Flame, sword: Target, 'calendar-check': Calendar, sunrise: Star };

export default function MemberGamification() {
  const { member } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/gamification/me`).then(res => setData(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center"><div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-white pb-24" data-testid="member-gamification-page">
      <div className="bg-zinc-900 border-b border-zinc-800 p-4 flex items-center gap-3">
        <button onClick={() => navigate('/app')} className="p-2 hover:bg-zinc-800 rounded-lg"><ArrowLeft size={20} /></button>
        <h1 className="font-bold text-lg">Mis Logros</h1>
      </div>

      <div className="p-4 space-y-6 max-w-lg mx-auto">
        {/* Points & Streak */}
        <div className="text-center py-4">
          <p className="text-5xl font-black" style={{ color: 'var(--gym-primary)' }}>{data?.points || 0}</p>
          <p className="text-zinc-400 text-sm">Puntos totales</p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-center">
            <Flame size={24} className="mx-auto text-orange-400 mb-1" />
            <p className="text-xl font-bold text-orange-400">{data?.current_streak || 0}</p>
            <p className="text-[10px] text-zinc-500">Racha actual</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-center">
            <Trophy size={24} className="mx-auto text-amber-400 mb-1" />
            <p className="text-xl font-bold text-amber-400">{data?.max_streak || 0}</p>
            <p className="text-[10px] text-zinc-500">Mejor racha</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-center">
            <Target size={24} className="mx-auto text-emerald-400 mb-1" />
            <p className="text-xl font-bold text-emerald-400">{data?.total_visits || 0}</p>
            <p className="text-[10px] text-zinc-500">Visitas</p>
          </div>
        </div>

        {/* Badges */}
        <div>
          <h2 className="text-lg font-bold mb-3 flex items-center gap-2"><Award size={20} style={{ color: 'var(--gym-primary)' }} /> Badges</h2>
          <div className="grid grid-cols-2 gap-3">
            {data?.all_badges?.map(badge => {
              const earned = data.earned_badges.includes(badge.id);
              const Icon = BADGE_ICONS[badge.icon] || Award;
              return (
                <div key={badge.id} className={`border rounded-xl p-3 flex items-center gap-3 transition-all ${earned ? 'border-amber-500/30 bg-amber-500/5' : 'border-zinc-800 bg-zinc-900/50 opacity-50'}`} data-testid={`badge-${badge.id}`}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${earned ? 'bg-amber-500/20' : 'bg-zinc-800'}`}>
                    {earned ? <Icon size={20} className="text-amber-400" /> : <Lock size={16} className="text-zinc-600" />}
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${earned ? 'text-zinc-200' : 'text-zinc-500'}`}>{badge.name}</p>
                    <p className="text-[10px] text-zinc-500">{badge.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
