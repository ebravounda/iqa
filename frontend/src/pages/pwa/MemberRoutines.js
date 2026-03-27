import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Dumbbell, ArrowLeft, ChevronDown, ChevronUp, CheckCircle, Circle } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MemberRoutines() {
  const navigate = useNavigate();
  const [routines, setRoutines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [completedExercises, setCompletedExercises] = useState({});

  useEffect(() => {
    axios.get(`${API}/routines/me`).then(res => setRoutines(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const toggleExercise = (routineId, dayIdx, exIdx) => {
    const key = `${routineId}-${dayIdx}-${exIdx}`;
    setCompletedExercises(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const logDay = async (routineId, dayIdx, exercises) => {
    const completed = exercises.map((ex, i) => ({ ...ex, done: !!completedExercises[`${routineId}-${dayIdx}-${i}`] })).filter(e => e.done);
    try {
      await axios.post(`${API}/routines/${routineId}/log`, { day_index: dayIdx, exercises_completed: completed.map(e => e.name) });
      toast.success('Dia registrado!');
    } catch { toast.error('Error'); }
  };

  if (loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center"><div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-white pb-24" data-testid="member-routines-page">
      <div className="bg-zinc-900 border-b border-zinc-800 p-4 flex items-center gap-3">
        <button onClick={() => navigate('/app')} className="p-2 hover:bg-zinc-800 rounded-lg"><ArrowLeft size={20} /></button>
        <h1 className="font-bold text-lg">Mis Rutinas</h1>
      </div>

      <div className="p-4 space-y-4 max-w-lg mx-auto">
        {routines.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">
            <Dumbbell size={48} className="mx-auto mb-4" />
            <p>Tu entrenador aun no te ha asignado rutinas</p>
          </div>
        ) : routines.map(r => (
          <div key={r.id} className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="p-4 cursor-pointer hover:bg-zinc-800/50" onClick={() => setExpanded(expanded === r.id ? null : r.id)}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold">{r.name}</h3>
                  {r.description && <p className="text-sm text-zinc-400">{r.description}</p>}
                  <p className="text-xs text-zinc-500 mt-1">Por: {r.trainer_name} - {r.days?.length || 0} dias</p>
                </div>
                {expanded === r.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </div>
            </div>
            {expanded === r.id && r.days?.map((day, di) => (
              <div key={di} className="border-t border-zinc-800 p-4">
                <h4 className="font-medium text-sm mb-3" style={{ color: 'var(--gym-primary)' }}>{day.name}</h4>
                <div className="space-y-2">
                  {day.exercises?.map((ex, ei) => {
                    const key = `${r.id}-${di}-${ei}`;
                    const done = completedExercises[key];
                    return (
                      <div key={ei} onClick={() => toggleExercise(r.id, di, ei)} className={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-all ${done ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-zinc-800/50'}`}>
                        {done ? <CheckCircle size={18} className="text-emerald-500 shrink-0" /> : <Circle size={18} className="text-zinc-600 shrink-0" />}
                        <div className="flex-1">
                          <p className={`text-sm ${done ? 'line-through text-zinc-500' : 'text-zinc-200'}`}>{ex.name}</p>
                          <p className="text-xs text-zinc-500">{ex.sets} series x {ex.reps} reps | {ex.rest}s descanso</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <Button onClick={() => logDay(r.id, di, day.exercises)} size="sm" className="btn-gym-primary mt-3 w-full">
                  Registrar dia completado
                </Button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
