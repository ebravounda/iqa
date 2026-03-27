import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import { Dumbbell, Plus, Trash2, ChevronDown, ChevronUp, User, Save, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminRoutines() {
  const { admin } = useAuth();
  const [routines, setRoutines] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', member_id: '', days: [] });

  const fetchData = useCallback(async () => {
    try {
      const [routRes, memRes] = await Promise.all([
        axios.get(`${API}/routines`),
        axios.get(`${API}/members?gym_id=${admin?.gym_id || ''}`)
      ]);
      setRoutines(routRes.data);
      setMembers(Array.isArray(memRes.data) ? memRes.data : memRes.data.members || []);
    } catch { toast.error('Error al cargar datos'); }
    finally { setLoading(false); }
  }, [admin]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const addDay = () => {
    setForm(f => ({ ...f, days: [...f.days, { name: `Dia ${f.days.length + 1}`, exercises: [{ name: '', sets: 3, reps: 12, rest: 60, notes: '' }] }] }));
  };

  const addExercise = (dayIdx) => {
    const days = [...form.days];
    days[dayIdx].exercises.push({ name: '', sets: 3, reps: 12, rest: 60, notes: '' });
    setForm(f => ({ ...f, days }));
  };

  const updateExercise = (dayIdx, exIdx, field, value) => {
    const days = [...form.days];
    days[dayIdx].exercises[exIdx][field] = value;
    setForm(f => ({ ...f, days }));
  };

  const removeExercise = (dayIdx, exIdx) => {
    const days = [...form.days];
    days[dayIdx].exercises.splice(exIdx, 1);
    setForm(f => ({ ...f, days }));
  };

  const removeDay = (dayIdx) => {
    const days = [...form.days];
    days.splice(dayIdx, 1);
    setForm(f => ({ ...f, days }));
  };

  const handleCreate = async () => {
    if (!form.name || !form.member_id) { toast.error('Nombre y socio son requeridos'); return; }
    try {
      await axios.post(`${API}/routines`, { ...form, gym_id: admin?.gym_id });
      toast.success('Rutina creada');
      setShowCreate(false);
      setForm({ name: '', description: '', member_id: '', days: [] });
      fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Error'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminar esta rutina?')) return;
    try {
      await axios.delete(`${API}/routines/${id}`);
      toast.success('Rutina eliminada');
      fetchData();
    } catch { toast.error('Error'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6" data-testid="admin-routines-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Dumbbell size={24} style={{ color: 'var(--gym-primary)' }} /> Rutinas</h1>
          <p className="text-zinc-400 text-sm">Asigna rutinas de entrenamiento a los socios</p>
        </div>
        <Button onClick={() => setShowCreate(true)} className="btn-gym-primary" data-testid="create-routine-btn">
          <Plus size={16} className="mr-2" /> Nueva Rutina
        </Button>
      </div>

      {routines.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <Dumbbell size={48} className="mx-auto mb-4" />
          <p>No hay rutinas creadas</p>
        </div>
      ) : (
        <div className="space-y-3">
          {routines.map(r => {
            const member = members.find(m => m.id === r.member_id);
            return (
              <div key={r.id} className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-zinc-800/30" onClick={() => setExpanded(expanded === r.id ? null : r.id)}>
                  <div>
                    <h3 className="font-bold text-zinc-200">{r.name}</h3>
                    <div className="flex items-center gap-2 text-sm text-zinc-400">
                      <User size={14} /> {member?.name || 'Socio'} - {r.days?.length || 0} dias - Por: {r.trainer_name}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button onClick={(e) => { e.stopPropagation(); handleDelete(r.id); }} variant="ghost" size="sm" className="text-red-400 hover:text-red-300">
                      <Trash2 size={14} />
                    </Button>
                    {expanded === r.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </div>
                {expanded === r.id && r.days && (
                  <div className="border-t border-zinc-800 p-4 space-y-3">
                    {r.days.map((day, di) => (
                      <div key={di} className="bg-zinc-800/50 rounded-lg p-3">
                        <h4 className="font-medium text-sm mb-2" style={{ color: 'var(--gym-primary)' }}>{day.name}</h4>
                        <div className="space-y-1">
                          {day.exercises?.map((ex, ei) => (
                            <div key={ei} className="flex items-center justify-between text-sm bg-zinc-900/50 rounded px-3 py-1.5">
                              <span className="text-zinc-300">{ex.name || 'Ejercicio'}</span>
                              <span className="text-zinc-500">{ex.sets}x{ex.reps} | {ex.rest}s rest</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="bg-zinc-900 border-zinc-700 text-white max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nueva Rutina</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Input placeholder="Nombre de la rutina" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-zinc-800 border-zinc-700" data-testid="routine-name-input" />
            <Input placeholder="Descripcion (opcional)" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="bg-zinc-800 border-zinc-700" />
            <select value={form.member_id} onChange={e => setForm({ ...form, member_id: e.target.value })} className="w-full bg-zinc-800 border border-zinc-700 text-zinc-300 rounded-lg px-3 py-2" data-testid="routine-member-select">
              <option value="">Seleccionar socio</option>
              {members.map(m => <option key={m.id} value={m.id}>{m.name} ({m.code})</option>)}
            </select>

            {/* Days */}
            {form.days.map((day, di) => (
              <div key={di} className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <Input value={day.name} onChange={e => { const d = [...form.days]; d[di].name = e.target.value; setForm({ ...form, days: d }); }} className="bg-zinc-900 border-zinc-600 font-medium w-40" />
                  <Button onClick={() => removeDay(di)} variant="ghost" size="sm" className="text-red-400"><X size={14} /></Button>
                </div>
                {day.exercises.map((ex, ei) => (
                  <div key={ei} className="flex gap-2 items-center">
                    <Input placeholder="Ejercicio" value={ex.name} onChange={e => updateExercise(di, ei, 'name', e.target.value)} className="bg-zinc-900 border-zinc-600 flex-1" />
                    <Input type="number" value={ex.sets} onChange={e => updateExercise(di, ei, 'sets', parseInt(e.target.value) || 0)} className="bg-zinc-900 border-zinc-600 w-16 text-center" placeholder="Sets" />
                    <Input type="number" value={ex.reps} onChange={e => updateExercise(di, ei, 'reps', parseInt(e.target.value) || 0)} className="bg-zinc-900 border-zinc-600 w-16 text-center" placeholder="Reps" />
                    <Button onClick={() => removeExercise(di, ei)} variant="ghost" size="sm" className="text-red-400"><Trash2 size={12} /></Button>
                  </div>
                ))}
                <Button onClick={() => addExercise(di)} variant="ghost" size="sm" className="text-zinc-400 text-xs"><Plus size={12} className="mr-1" /> Ejercicio</Button>
              </div>
            ))}

            <Button onClick={addDay} variant="outline" size="sm" className="w-full border-zinc-600 text-zinc-300"><Plus size={14} className="mr-2" /> Agregar Dia</Button>
            <Button onClick={handleCreate} className="btn-gym-primary w-full" data-testid="save-routine-btn"><Save size={16} className="mr-2" /> Guardar Rutina</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
