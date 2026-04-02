import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useBusiness } from '../../context/BusinessContext';
import { getPlans, createPlan, deletePlan, updatePlan, getGyms } from '../../lib/api';
import { formatCurrency } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Plus, Trash2, Calendar, Clock, Building2, ChevronDown, ChevronRight, Pencil, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminPlans() {
  const { admin, isSuperAdmin } = useAuth();
  const { labels } = useBusiness();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPlan, setNewPlan] = useState({
    name: '', description: '', price: '', duration_days: '', access_type: 'unlimited', gym_id: ''
  });
  const [gyms, setGyms] = useState([]);
  const [collapsedGyms, setCollapsedGyms] = useState({});
  const [editPlan, setEditPlan] = useState(null);

  useEffect(() => {
    fetchPlans();
    if (isSuperAdmin) fetchGyms();
  }, []);

  const fetchGyms = async () => {
    try {
      const response = await getGyms();
      setGyms(response.data);
    } catch (error) {
      console.error('Error fetching gyms:', error);
    }
  };

  const fetchPlans = async () => {
    try {
      const gymId = isSuperAdmin ? null : admin?.gym_id;
      const response = await getPlans(gymId);
      setPlans(response.data);
    } catch (error) {
      toast.error('Error al cargar planes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async () => {
    if (!newPlan.name || !newPlan.price || !newPlan.duration_days) {
      toast.error('Nombre, precio y duracion son requeridos');
      return;
    }
    const gymId = isSuperAdmin ? newPlan.gym_id : admin?.gym_id;
    if (!gymId) { toast.error('Selecciona un gimnasio'); return; }
    try {
      if (editPlan) {
        await updatePlan(editPlan.id, { ...newPlan, price: parseFloat(newPlan.price), duration_days: parseInt(newPlan.duration_days) });
        toast.success('Plan actualizado');
      } else {
        await createPlan({ ...newPlan, gym_id: gymId, price: parseFloat(newPlan.price), duration_days: parseInt(newPlan.duration_days) });
        toast.success('Plan creado exitosamente');
      }
      setShowCreateModal(false);
      setEditPlan(null);
      setNewPlan({ name: '', description: '', price: '', duration_days: '', access_type: 'unlimited', gym_id: '' });
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error');
    }
  };

  const openEditPlan = (plan) => {
    setEditPlan(plan);
    setNewPlan({
      name: plan.name || '',
      description: plan.description || '',
      price: plan.price?.toString() || '',
      duration_days: plan.duration_days?.toString() || '',
      access_type: plan.access_type || 'unlimited',
      gym_id: plan.gym_id || ''
    });
    setShowCreateModal(true);
  };

  const handleDeletePlan = async (planId) => {
    if (!window.confirm('Eliminar este plan?')) return;
    try { await deletePlan(planId); toast.success('Plan eliminado'); fetchPlans(); }
    catch (error) { toast.error('Error al eliminar plan'); }
  };

  const getDurationLabel = (days) => {
    if (days === 1) return '1 dia';
    if (days === 7) return '1 semana';
    if (days === 30) return '1 mes';
    if (days === 90) return '3 meses';
    if (days === 180) return '6 meses';
    if (days === 365) return '1 ano';
    return `${days} dias`;
  };

  const toggleGym = (gymId) => setCollapsedGyms(prev => ({ ...prev, [gymId]: !prev[gymId] }));

  // Group plans by gym
  const plansByGym = {};
  plans.forEach(plan => {
    const gid = plan.gym_id || 'unknown';
    if (!plansByGym[gid]) plansByGym[gid] = [];
    plansByGym[gid].push(plan);
  });

  const getGymName = (gymId) => {
    const gym = gyms.find(g => g.id === gymId);
    return gym?.name || gymId;
  };

  return (
    <div className="space-y-6" data-testid="admin-plans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">{labels.plans} de {labels.membership}</h1>
          <p style={{ color: 'var(--text-secondary)' }} className="text-sm">{plans.length} {labels.plans.toLowerCase()} en {Object.keys(plansByGym).length} negocio(s)</p>
        </div>
        <Dialog open={showCreateModal} onOpenChange={(v) => { setShowCreateModal(v); if (!v) setEditPlan(null); }}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-plan-btn" onClick={() => { setEditPlan(null); setNewPlan({ name: '', description: '', price: '', duration_days: '', access_type: 'unlimited', gym_id: '' }); }}>
              <Plus size={20} className="mr-2" /> Nuevo Plan
            </Button>
          </DialogTrigger>
          <DialogContent style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
            <DialogHeader>
              <DialogTitle>{editPlan ? 'Editar Plan' : 'Crear Nuevo Plan'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {isSuperAdmin && (
                <div>
                  <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Gimnasio *</label>
                  <Select value={newPlan.gym_id || "none"} onValueChange={(v) => setNewPlan({ ...newPlan, gym_id: v === "none" ? "" : v })}>
                    <SelectTrigger style={{ background: 'var(--bg-tertiary)', borderColor: 'var(--border-secondary)' }} data-testid="plan-gym-select">
                      <SelectValue placeholder="Seleccionar gimnasio" />
                    </SelectTrigger>
                    <SelectContent style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-secondary)' }}>
                      <SelectItem value="none">Seleccionar...</SelectItem>
                      {gyms.map((g) => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Nombre del Plan</label>
                <Input value={newPlan.name} onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })} placeholder="Ej: Plan Mensual" className="input-dark" data-testid="plan-name-input" />
              </div>
              <div>
                <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Descripcion (opcional)</label>
                <Input value={newPlan.description} onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })} placeholder="Acceso ilimitado al gimnasio" className="input-dark" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Precio</label>
                  <Input type="number" step="0.01" value={newPlan.price} onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })} placeholder="30.00" className="input-dark" data-testid="plan-price-input" />
                </div>
                <div>
                  <label className="text-sm mb-1 block" style={{ color: 'var(--text-secondary)' }}>Duracion (dias)</label>
                  <Input type="number" value={newPlan.duration_days} onChange={(e) => setNewPlan({ ...newPlan, duration_days: e.target.value })} placeholder="30" className="input-dark" data-testid="plan-duration-input" />
                </div>
              </div>
              <div className="flex gap-2 flex-wrap">
                {[{ days: 1, label: '1 dia' }, { days: 7, label: '1 semana' }, { days: 30, label: '1 mes' }, { days: 90, label: '3 meses' }, { days: 365, label: '1 ano' }].map((preset) => (
                  <button key={preset.days} type="button" onClick={() => setNewPlan({ ...newPlan, duration_days: preset.days.toString() })}
                    className="px-3 py-1 rounded-full text-xs border transition-colors"
                    style={newPlan.duration_days === preset.days.toString()
                      ? { borderColor: 'var(--gym-primary)', color: 'var(--gym-primary)' }
                      : { borderColor: 'var(--border-secondary)', color: 'var(--text-secondary)' }
                    }>{preset.label}</button>
                ))}
              </div>
              <Button onClick={handleCreatePlan} className="w-full btn-gym-primary" data-testid="save-plan-btn">
                {editPlan ? <><Pencil size={20} className="mr-2" /> Guardar Cambios</> : <><Plus size={20} className="mr-2" /> Crear Plan</>}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => <div key={i} className="stat-card"><div className="skeleton h-6 w-32 mb-4" /><div className="skeleton h-10 w-24 mb-4" /><div className="skeleton h-4 w-full" /></div>)}
        </div>
      ) : plans.length === 0 ? (
        <div className="text-center py-12">
          <Calendar size={48} className="mx-auto mb-4" style={{ color: 'var(--text-dim)' }} />
          <p style={{ color: 'var(--text-muted)' }}>No hay planes creados</p>
          <p style={{ color: 'var(--text-dim)' }} className="text-sm">Crea tu primer plan de membresia</p>
        </div>
      ) : isSuperAdmin ? (
        // SUPER ADMIN: grouped by gym
        <div className="space-y-4">
          {Object.entries(plansByGym).map(([gymId, gymPlans]) => (
            <div key={gymId} className="stat-card" data-testid={`gym-plans-${gymId}`}>
              <button onClick={() => toggleGym(gymId)} className="w-full flex items-center gap-3 mb-4 text-left" data-testid={`toggle-gym-${gymId}`}>
                <Building2 size={20} style={{ color: 'var(--gym-primary)' }} />
                <h2 className="text-lg font-bold flex-1">{getGymName(gymId)}</h2>
                <span className="text-xs px-2 py-1 rounded-full" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>{gymPlans.length} plan(es)</span>
                {collapsedGyms[gymId] ? <ChevronRight size={18} style={{ color: 'var(--text-muted)' }} /> : <ChevronDown size={18} style={{ color: 'var(--text-muted)' }} />}
              </button>
              {!collapsedGyms[gymId] && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {gymPlans.map((plan) => (
                    <div key={plan.id} className="relative group p-4 rounded-xl border transition-colors" style={{ background: 'var(--bg-tertiary)', borderColor: 'var(--border-primary)' }}>
                      <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => openEditPlan(plan)} className="p-1.5 rounded-lg hover:text-blue-400" style={{ background: 'var(--bg-secondary)' }} data-testid={`edit-plan-${plan.id}`}>
                          <Pencil size={14} />
                        </button>
                        <button onClick={() => handleDeletePlan(plan.id)} className="p-1.5 rounded-lg hover:text-red-500" style={{ background: 'var(--bg-secondary)' }} data-testid={`delete-plan-${plan.id}`}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                      <h3 className="font-bold mb-2">{plan.name}</h3>
                      <div className="flex items-baseline gap-1 mb-3">
                        <span className="text-3xl font-black" style={{ color: 'var(--gym-primary)' }}>{formatCurrency(plan.price)}</span>
                      </div>
                      <div className="space-y-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <div className="flex items-center gap-2"><Clock size={14} /><span>{getDurationLabel(plan.duration_days)}</span></div>
                        {plan.description && <p className="pt-2 border-t" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>{plan.description}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        // GYM ADMIN: flat grid
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div key={plan.id} className="stat-card relative group">
              <div className="absolute top-4 right-4 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => openEditPlan(plan)} className="p-2 rounded-lg hover:text-blue-400" style={{ background: 'var(--bg-tertiary)' }} data-testid={`edit-plan-${plan.id}`}>
                  <Pencil size={16} />
                </button>
                <button onClick={() => handleDeletePlan(plan.id)} className="p-2 rounded-lg hover:text-red-500" style={{ background: 'var(--bg-tertiary)' }} data-testid={`delete-plan-${plan.id}`}>
                  <Trash2 size={16} />
                </button>
              </div>
              <h3 className="font-bold text-lg mb-2">{plan.name}</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-black" style={{ color: 'var(--gym-primary)' }}>{formatCurrency(plan.price)}</span>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2" style={{ color: 'var(--text-secondary)' }}><Clock size={16} /><span>{getDurationLabel(plan.duration_days)}</span></div>
                <div className="flex items-center gap-2" style={{ color: 'var(--text-secondary)' }}><DollarSign size={16} /><span>{formatCurrency((plan.price || 0) / (plan.duration_days || 1))}/dia</span></div>
                {plan.description && <p className="pt-2 border-t" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>{plan.description}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
