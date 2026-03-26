import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getSaaSPlans, createSaaSPlan, updateSaaSPlan, deleteSaaSPlan, getGyms, assignSaaSPlan } from '../../lib/api';
import { toast } from 'sonner';

const CURRENCY_OPTIONS = [
  { code: 'EUR', symbol: '\u20ac', name: 'Euro', decimals: 2 },
  { code: 'USD', symbol: '$', name: 'Dolar US', decimals: 2 },
  { code: 'CLP', symbol: '$', name: 'Peso Chileno', decimals: 0 },
  { code: 'ARS', symbol: '$', name: 'Peso Argentino', decimals: 2 },
];

export default function AdminSaaSPlans() {
  const { admin } = useAuth();
  const isSuperAdmin = admin?.role === 'super_admin';
  const [plans, setPlans] = useState([]);
  const [gyms, setGyms] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editPlan, setEditPlan] = useState(null);
  const [assignGym, setAssignGym] = useState(null);
  const [form, setForm] = useState({ name: '', max_members: 500, has_pos: false, has_mercadopago: false, has_iframes: false, has_advanced_accounting: false, price_monthly: 0, currency: 'EUR', description: '' });

  const load = useCallback(async () => {
    try {
      const [p, g] = await Promise.all([getSaaSPlans(), getGyms()]);
      setPlans(p.data);
      setGyms(g.data);
    } catch (e) { toast.error('Error al cargar planes'); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!isSuperAdmin) return <div className="p-6 text-zinc-400">Solo el Super Admin puede gestionar planes SaaS.</div>;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editPlan) {
        await updateSaaSPlan(editPlan.id, form);
        toast.success('Plan actualizado');
      } else {
        await createSaaSPlan(form);
        toast.success('Plan creado');
      }
      setShowForm(false); setEditPlan(null);
      setForm({ name: '', max_members: 500, has_pos: false, has_mercadopago: false, has_iframes: false, has_advanced_accounting: false, price_monthly: 0, currency: 'EUR', description: '' });
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminar este plan SaaS?')) return;
    try { await deleteSaaSPlan(id); toast.success('Plan eliminado'); load(); }
    catch (e) { toast.error('Error'); }
  };

  const handleAssign = async (gymId, planId) => {
    try { await assignSaaSPlan(gymId, planId); toast.success('Plan asignado'); setAssignGym(null); load(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Error al asignar'); }
  };

  const cur = (code) => CURRENCY_OPTIONS.find(c => c.code === code) || CURRENCY_OPTIONS[0];

  return (
    <div className="space-y-6" data-testid="saas-plans-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Planes SaaS</h1>
          <p className="text-zinc-400 text-sm">Define los planes y limites para cada gimnasio</p>
        </div>
        <button onClick={() => { setShowForm(true); setEditPlan(null); setForm({ name: '', max_members: 500, has_pos: false, has_mercadopago: false, has_iframes: false, has_advanced_accounting: false, price_monthly: 0, currency: 'EUR', description: '' }); }} className="btn-gym-primary" data-testid="create-saas-plan-btn">
          + Nuevo Plan
        </button>
      </div>

      {showForm && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6" data-testid="saas-plan-form">
          <h3 className="text-lg font-bold text-white mb-4">{editPlan ? 'Editar' : 'Nuevo'} Plan SaaS</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input-gym" placeholder="Nombre del plan" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required data-testid="saas-plan-name" />
            <input className="input-gym" type="number" placeholder="Max socios" value={form.max_members} onChange={e => setForm({ ...form, max_members: parseInt(e.target.value) })} data-testid="saas-plan-max-members" />
            <input className="input-gym" type="number" step="0.01" placeholder="Precio mensual" value={form.price_monthly} onChange={e => setForm({ ...form, price_monthly: parseFloat(e.target.value) })} data-testid="saas-plan-price" />
            <select className="input-gym" value={form.currency} onChange={e => setForm({ ...form, currency: e.target.value })} data-testid="saas-plan-currency">
              {CURRENCY_OPTIONS.map(c => <option key={c.code} value={c.code}>{c.code} - {c.name}</option>)}
            </select>
            <textarea className="input-gym col-span-full" placeholder="Descripcion" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} data-testid="saas-plan-description" />
            <div className="col-span-full grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { key: 'has_pos', label: 'TPV/POS' },
                { key: 'has_mercadopago', label: 'MercadoPago' },
                { key: 'has_iframes', label: 'Iframes' },
                { key: 'has_advanced_accounting', label: 'Contab. Avanzada' },
              ].map(f => (
                <label key={f.key} className="flex items-center gap-2 bg-zinc-800 p-3 rounded-lg cursor-pointer hover:bg-zinc-700 transition-colors">
                  <input type="checkbox" checked={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.checked })} className="accent-[var(--gym-primary)]" />
                  <span className="text-sm text-zinc-300">{f.label}</span>
                </label>
              ))}
            </div>
            <div className="col-span-full flex gap-3">
              <button type="submit" className="btn-gym-primary" data-testid="save-saas-plan-btn">{editPlan ? 'Actualizar' : 'Crear'} Plan</button>
              <button type="button" onClick={() => { setShowForm(false); setEditPlan(null); }} className="btn-gym-secondary">Cancelar</button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {plans.map(plan => (
          <div key={plan.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 hover:border-zinc-600 transition-colors" data-testid={`saas-plan-${plan.id}`}>
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-white">{plan.name}</h3>
              <span className="text-[var(--gym-primary)] font-bold">{cur(plan.currency).symbol}{plan.price_monthly}/{plan.currency === 'CLP' ? 'mes' : 'mo'}</span>
            </div>
            {plan.description && <p className="text-zinc-400 text-sm mb-3">{plan.description}</p>}
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm"><span className="text-zinc-400">Max Socios</span><span className="text-white font-mono">{plan.max_members.toLocaleString()}</span></div>
              <div className="flex flex-wrap gap-2">
                {plan.has_pos && <span className="badge-feature">TPV</span>}
                {plan.has_mercadopago && <span className="badge-feature">MercadoPago</span>}
                {plan.has_iframes && <span className="badge-feature">Iframes</span>}
                {plan.has_advanced_accounting && <span className="badge-feature">Contabilidad</span>}
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { setEditPlan(plan); setForm(plan); setShowForm(true); }} className="text-xs px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700">Editar</button>
              <button onClick={() => handleDelete(plan.id)} className="text-xs px-3 py-1.5 rounded-lg bg-red-900/30 text-red-400 hover:bg-red-900/50">Eliminar</button>
              <button onClick={() => setAssignGym(plan.id)} className="text-xs px-3 py-1.5 rounded-lg bg-[var(--gym-primary)]/20 text-[var(--gym-primary)] hover:bg-[var(--gym-primary)]/30">Asignar Gym</button>
            </div>
          </div>
        ))}
        {plans.length === 0 && <p className="text-zinc-500 col-span-full text-center py-8">No hay planes SaaS. Crea el primero.</p>}
      </div>

      {assignGym && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" data-testid="assign-plan-modal">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-bold text-white mb-4">Asignar Plan a Gimnasio</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {gyms.map(gym => (
                <button key={gym.id} onClick={() => handleAssign(gym.id, assignGym)} className="w-full text-left p-3 bg-zinc-800 rounded-lg hover:bg-zinc-700 transition-colors" data-testid={`assign-gym-${gym.id}`}>
                  <span className="text-white font-semibold">{gym.name}</span>
                  {gym.saas_plan_name && <span className="text-zinc-400 text-xs ml-2">({gym.saas_plan_name})</span>}
                </button>
              ))}
            </div>
            <button onClick={() => setAssignGym(null)} className="mt-4 w-full btn-gym-secondary">Cerrar</button>
          </div>
        </div>
      )}
    </div>
  );
}
