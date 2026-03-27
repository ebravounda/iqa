import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getSaaSPlans, createSaaSPlan, updateSaaSPlan, deleteSaaSPlan, getGyms, assignSaaSPlan } from '../../lib/api';
import { toast } from 'sonner';
import { QrCode, Users, Calendar, ShoppingCart, BarChart3, Trophy, Dumbbell, Mail, CreditCard, Code, DollarSign, Shield, Check, X as XIcon } from 'lucide-react';

const CURRENCY_OPTIONS = [
  { code: 'EUR', symbol: '\u20ac', name: 'Euro' },
  { code: 'USD', symbol: '$', name: 'Dolar US' },
  { code: 'CLP', symbol: '$', name: 'Peso Chileno' },
  { code: 'ARS', symbol: '$', name: 'Peso Argentino' },
];

const FEATURES = [
  { key: 'has_qr_access', label: 'Control de Acceso QR', icon: QrCode, always: true },
  { key: 'has_guest_passes', label: 'Pases de Invitados', icon: Users },
  { key: 'has_classes', label: 'Clases y Reservas', icon: Calendar },
  { key: 'has_pos', label: 'TPV / Punto de Venta', icon: ShoppingCart },
  { key: 'has_analytics', label: 'Analytics Avanzado', icon: BarChart3 },
  { key: 'has_gamification', label: 'Gamificacion', icon: Trophy },
  { key: 'has_routines', label: 'Rutinas de Ejercicio', icon: Dumbbell },
  { key: 'has_email_smtp', label: 'Emails Automaticos (SMTP)', icon: Mail },
  { key: 'has_stripe_members', label: 'Pagos Stripe (Socios)', icon: CreditCard },
  { key: 'has_mercadopago', label: 'MercadoPago', icon: DollarSign },
  { key: 'has_iframes', label: 'Iframes Personalizados', icon: Code },
  { key: 'has_advanced_accounting', label: 'Contabilidad Avanzada', icon: Shield },
];

const defaultForm = {
  name: '', max_members: 500, price_monthly: 0, currency: 'EUR', description: '',
  has_qr_access: true, has_guest_passes: false, has_classes: false, has_pos: false,
  has_analytics: false, has_gamification: false, has_routines: false, has_email_smtp: false,
  has_stripe_members: false, has_mercadopago: false, has_iframes: false, has_advanced_accounting: false
};

export default function AdminSaaSPlans() {
  const { admin } = useAuth();
  const isSuperAdmin = admin?.role === 'super_admin';
  const [plans, setPlans] = useState([]);
  const [gyms, setGyms] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editPlan, setEditPlan] = useState(null);
  const [assignGym, setAssignGym] = useState(null);
  const [form, setForm] = useState({ ...defaultForm });

  const load = useCallback(async () => {
    try {
      const [p, g] = await Promise.all([getSaaSPlans(), getGyms()]);
      setPlans(p.data);
      setGyms(g.data);
    } catch (e) { toast.error('Error al cargar planes'); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!isSuperAdmin) return <div className="p-6" style={{ color: 'var(--text-secondary)' }}>Solo el Super Admin puede gestionar planes SaaS.</div>;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name) { toast.error('El nombre es requerido'); return; }
    try {
      if (editPlan) {
        await updateSaaSPlan(editPlan.id, form);
        toast.success('Plan actualizado');
      } else {
        await createSaaSPlan(form);
        toast.success('Plan creado');
      }
      setShowForm(false); setEditPlan(null); setForm({ ...defaultForm });
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
  const countFeatures = (plan) => FEATURES.filter(f => plan[f.key]).length;

  return (
    <div className="space-y-6" data-testid="saas-plans-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black">Planes SaaS</h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Define planes, limites y precios para cada gimnasio</p>
        </div>
        <button onClick={() => { setShowForm(true); setEditPlan(null); setForm({ ...defaultForm }); }} className="btn-gym-primary" data-testid="create-saas-plan-btn">
          + Nuevo Plan SaaS
        </button>
      </div>

      {/* Create/Edit Form */}
      {showForm && (
        <div className="rounded-xl p-6" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }} data-testid="saas-plan-form">
          <h3 className="text-lg font-bold mb-4">{editPlan ? 'Editar' : 'Nuevo'} Plan SaaS</h3>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Nombre del Plan *</label>
                <input className="input-gym" placeholder="Ej: Plan Inicial" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required data-testid="saas-plan-name" />
              </div>
              <div>
                <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Max. Socios</label>
                <input className="input-gym" type="number" placeholder="500" value={form.max_members} onChange={e => setForm({ ...form, max_members: parseInt(e.target.value) || 0 })} data-testid="saas-plan-max-members" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Precio/mes</label>
                  <input className="input-gym" type="number" step="0.01" placeholder="49.99" value={form.price_monthly} onChange={e => setForm({ ...form, price_monthly: parseFloat(e.target.value) || 0 })} data-testid="saas-plan-price" />
                </div>
                <div>
                  <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Moneda</label>
                  <select className="input-gym" value={form.currency} onChange={e => setForm({ ...form, currency: e.target.value })} data-testid="saas-plan-currency">
                    {CURRENCY_OPTIONS.map(c => <option key={c.code} value={c.code}>{c.code}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <div>
              <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Descripcion</label>
              <textarea className="input-gym w-full" placeholder="Ideal para gimnasios pequenos..." value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} data-testid="saas-plan-description" />
            </div>
            <div>
              <label className="text-sm mb-2 block font-medium" style={{ color: 'var(--text-secondary)' }}>Caracteristicas incluidas</label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {FEATURES.map(f => {
                  const Icon = f.icon;
                  const checked = f.always || form[f.key];
                  return (
                    <label key={f.key} className="flex items-center gap-2.5 p-3 rounded-lg cursor-pointer transition-colors" style={{ background: checked ? 'rgba(225,255,1,0.08)' : 'var(--bg-tertiary)', border: `1px solid ${checked ? 'rgba(225,255,1,0.3)' : 'var(--border-primary)'}` }}>
                      <input type="checkbox" checked={checked} disabled={f.always} onChange={e => setForm({ ...form, [f.key]: e.target.checked })} className="accent-[var(--gym-primary)]" />
                      <Icon size={16} style={{ color: checked ? 'var(--gym-primary)' : 'var(--text-muted)' }} />
                      <span className="text-sm" style={{ color: checked ? 'var(--text-primary)' : 'var(--text-muted)' }}>{f.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" className="btn-gym-primary" data-testid="save-saas-plan-btn">{editPlan ? 'Actualizar' : 'Crear'} Plan</button>
              <button type="button" onClick={() => { setShowForm(false); setEditPlan(null); }} className="btn-gym-secondary">Cancelar</button>
            </div>
          </form>
        </div>
      )}

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {plans.map(plan => {
          const assignedGyms = gyms.filter(g => g.saas_plan_id === plan.id);
          return (
            <div key={plan.id} className="rounded-xl p-5 transition-colors" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }} data-testid={`saas-plan-${plan.id}`}>
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-bold">{plan.name}</h3>
                <span className="font-bold" style={{ color: 'var(--gym-primary)' }}>
                  {plan.price_monthly > 0 ? `${cur(plan.currency).symbol}${plan.price_monthly}/mes` : 'Gratis'}
                </span>
              </div>
              {plan.description && <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>{plan.description}</p>}
              
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--text-secondary)' }}>Max Socios</span>
                  <span className="font-mono font-bold">{plan.max_members?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--text-secondary)' }}>Caracteristicas</span>
                  <span className="font-bold">{countFeatures(plan)}/{FEATURES.length}</span>
                </div>
              </div>

              {/* Features compact list */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {FEATURES.map(f => plan[f.key] ? (
                  <span key={f.key} className="badge-feature text-[10px]">{f.label.split(' ')[0]}</span>
                ) : null)}
              </div>

              {/* Assigned gyms */}
              {assignedGyms.length > 0 && (
                <div className="mb-3 p-2 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Gimnasios con este plan:</p>
                  {assignedGyms.map(g => (
                    <span key={g.id} className="inline-block text-xs mr-1 mb-1 px-2 py-0.5 rounded" style={{ background: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>{g.name}</span>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <button onClick={() => { setEditPlan(plan); setForm({ ...defaultForm, ...plan }); setShowForm(true); }} className="text-xs px-3 py-1.5 rounded-lg transition-colors" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>Editar</button>
                <button onClick={() => handleDelete(plan.id)} className="text-xs px-3 py-1.5 rounded-lg bg-red-900/30 text-red-400 hover:bg-red-900/50">Eliminar</button>
                <button onClick={() => setAssignGym(plan.id)} className="text-xs px-3 py-1.5 rounded-lg" style={{ background: 'rgba(225,255,1,0.1)', color: 'var(--gym-primary)' }}>Asignar Gym</button>
              </div>
            </div>
          );
        })}
        {plans.length === 0 && <p className="col-span-full text-center py-8" style={{ color: 'var(--text-muted)' }}>No hay planes SaaS. Crea el primero.</p>}
      </div>

      {/* Assign Modal */}
      {assignGym && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'var(--modal-bg)' }} data-testid="assign-plan-modal">
          <div className="rounded-xl p-6 w-full max-w-md" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-secondary)' }}>
            <h3 className="text-lg font-bold mb-4">Asignar Plan a Gimnasio</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {gyms.map(gym => (
                <button key={gym.id} onClick={() => handleAssign(gym.id, assignGym)} className="w-full text-left p-3 rounded-lg transition-colors" style={{ background: 'var(--bg-tertiary)' }} data-testid={`assign-gym-${gym.id}`}>
                  <span className="font-semibold">{gym.name}</span>
                  {gym.saas_plan_name && <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>({gym.saas_plan_name})</span>}
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
