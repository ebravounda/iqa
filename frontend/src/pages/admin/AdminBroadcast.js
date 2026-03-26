import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { createBroadcast, getActiveBroadcasts, dismissBroadcast } from '../../lib/api';
import { toast } from 'sonner';

export default function AdminBroadcast() {
  const { admin } = useAuth();
  const isSuperAdmin = admin?.role === 'super_admin';
  const [broadcasts, setBroadcasts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', message: '', priority: 'normal' });

  const load = useCallback(async () => {
    try {
      const { data } = await getActiveBroadcasts();
      setBroadcasts(data);
    } catch (e) {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createBroadcast(form);
      toast.success('Broadcast enviado a todos los gimnasios');
      setShowForm(false);
      setForm({ title: '', message: '', priority: 'normal' });
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const handleDismiss = async (id) => {
    try { await dismissBroadcast(id); load(); }
    catch (e) {}
  };

  return (
    <div className="space-y-6" data-testid="broadcast-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Comunicados</h1>
          <p className="text-zinc-400 text-sm">Mensajes globales para todos los gimnasios</p>
        </div>
        {isSuperAdmin && (
          <button onClick={() => setShowForm(!showForm)} className="btn-gym-primary" data-testid="create-broadcast-btn">+ Nuevo Comunicado</button>
        )}
      </div>

      {showForm && isSuperAdmin && (
        <form onSubmit={handleCreate} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-4" data-testid="broadcast-form">
          <input className="input-gym w-full" placeholder="Titulo" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required data-testid="broadcast-title" />
          <textarea className="input-gym w-full" placeholder="Mensaje" value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} rows={4} required data-testid="broadcast-message" />
          <div className="flex items-center gap-4">
            <label className="text-zinc-400 text-sm">Prioridad:</label>
            {['normal', 'urgent'].map(p => (
              <label key={p} className="flex items-center gap-1 text-sm text-zinc-300 cursor-pointer">
                <input type="radio" name="priority" value={p} checked={form.priority === p} onChange={e => setForm({ ...form, priority: e.target.value })} className="accent-[var(--gym-primary)]" />
                {p === 'normal' ? 'Normal' : 'Urgente'}
              </label>
            ))}
          </div>
          <div className="flex gap-3">
            <button type="submit" className="btn-gym-primary" data-testid="send-broadcast-btn">Enviar Comunicado</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-gym-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {broadcasts.map(b => (
          <div key={b.id} className={`bg-zinc-900 border rounded-xl p-5 ${b.priority === 'urgent' ? 'border-red-600' : 'border-zinc-800'}`} data-testid={`broadcast-${b.id}`}>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  {b.priority === 'urgent' && <span className="text-xs px-2 py-0.5 rounded bg-red-900/30 text-red-400">URGENTE</span>}
                  <h3 className="text-lg font-bold text-white">{b.title}</h3>
                </div>
                <p className="text-zinc-300">{b.message}</p>
                <p className="text-zinc-500 text-xs mt-2">{new Date(b.created_at).toLocaleString()}</p>
              </div>
              <button onClick={() => handleDismiss(b.id)} className="text-zinc-400 hover:text-white text-sm" data-testid={`dismiss-${b.id}`}>Ocultar</button>
            </div>
          </div>
        ))}
        {broadcasts.length === 0 && <p className="text-zinc-500 text-center py-8">No hay comunicados activos</p>}
      </div>
    </div>
  );
}
