import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getPlans, createPlan, deletePlan, getGyms } from '../../lib/api';
import { formatCurrency } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Plus, Trash2, Calendar, DollarSign, Clock } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminPlans() {
  const { admin, isSuperAdmin } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPlan, setNewPlan] = useState({
    name: '',
    description: '',
    price: '',
    duration_days: '',
    access_type: 'unlimited',
    gym_id: ''
  });
  const [gyms, setGyms] = useState([]);

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

  useEffect(() => {
    fetchPlans();
  }, []);

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
      toast.error('Nombre, precio y duración son requeridos');
      return;
    }

    const gymId = isSuperAdmin ? newPlan.gym_id : admin?.gym_id;
    if (!gymId) {
      toast.error('Selecciona un gimnasio');
      return;
    }

    try {
      await createPlan({
        ...newPlan,
        gym_id: gymId,
        price: parseFloat(newPlan.price),
        duration_days: parseInt(newPlan.duration_days)
      });
      toast.success('Plan creado exitosamente');
      setShowCreateModal(false);
      setNewPlan({ name: '', description: '', price: '', duration_days: '', access_type: 'unlimited', gym_id: '' });
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear plan');
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!window.confirm('¿Estás seguro de eliminar este plan?')) return;
    
    try {
      await deletePlan(planId);
      toast.success('Plan eliminado');
      fetchPlans();
    } catch (error) {
      toast.error('Error al eliminar plan');
    }
  };

  const getDurationLabel = (days) => {
    if (days === 1) return '1 día';
    if (days === 7) return '1 semana';
    if (days === 30) return '1 mes';
    if (days === 90) return '3 meses';
    if (days === 180) return '6 meses';
    if (days === 365) return '1 año';
    return `${days} días`;
  };

  return (
    <div className="space-y-6" data-testid="admin-plans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Planes de Membresía</h1>
          <p className="text-zinc-400 text-sm">{plans.length} planes activos</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-plan-btn">
              <Plus size={20} className="mr-2" />
              Nuevo Plan
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Plan</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {isSuperAdmin && (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Gimnasio *</label>
                  <Select value={newPlan.gym_id || "none"} onValueChange={(v) => setNewPlan({ ...newPlan, gym_id: v === "none" ? "" : v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="plan-gym-select">
                      <SelectValue placeholder="Seleccionar gimnasio" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="none">Seleccionar...</SelectItem>
                      {gyms.map((g) => (
                        <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre del Plan</label>
                <Input
                  value={newPlan.name}
                  onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })}
                  placeholder="Ej: Plan Mensual"
                  className="input-dark"
                  data-testid="plan-name-input"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Descripción (opcional)</label>
                <Input
                  value={newPlan.description}
                  onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })}
                  placeholder="Acceso ilimitado al gimnasio"
                  className="input-dark"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Precio (USD)</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newPlan.price}
                    onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })}
                    placeholder="30.00"
                    className="input-dark"
                    data-testid="plan-price-input"
                  />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Duración (días)</label>
                  <Input
                    type="number"
                    value={newPlan.duration_days}
                    onChange={(e) => setNewPlan({ ...newPlan, duration_days: e.target.value })}
                    placeholder="30"
                    className="input-dark"
                    data-testid="plan-duration-input"
                  />
                </div>
              </div>
              <div className="flex gap-2 flex-wrap">
                {[
                  { days: 1, label: '1 día' },
                  { days: 7, label: '1 semana' },
                  { days: 30, label: '1 mes' },
                  { days: 90, label: '3 meses' },
                  { days: 365, label: '1 año' }
                ].map((preset) => (
                  <button
                    key={preset.days}
                    type="button"
                    onClick={() => setNewPlan({ ...newPlan, duration_days: preset.days.toString() })}
                    className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                      newPlan.duration_days === preset.days.toString()
                        ? 'border-[var(--gym-primary)] text-[var(--gym-primary)]'
                        : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                    }`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              <Button onClick={handleCreatePlan} className="w-full btn-gym-primary" data-testid="save-plan-btn">
                <Plus size={20} className="mr-2" />
                Crear Plan
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-6 w-32 mb-4" />
              <div className="skeleton h-10 w-24 mb-4" />
              <div className="skeleton h-4 w-full" />
            </div>
          ))
        ) : plans.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Calendar size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay planes creados</p>
            <p className="text-zinc-600 text-sm">Crea tu primer plan de membresía</p>
          </div>
        ) : (
          plans.map((plan) => (
            <div key={plan.id} className="stat-card relative group">
              <button
                onClick={() => handleDeletePlan(plan.id)}
                className="absolute top-4 right-4 p-2 rounded-lg bg-zinc-800 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/20 hover:text-red-500"
                data-testid={`delete-plan-${plan.id}`}
              >
                <Trash2 size={16} />
              </button>
              
              <h3 className="font-bold text-lg mb-2">{plan.name}</h3>
              
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-black" style={{ color: 'var(--gym-primary)' }}>
                  {formatCurrency(plan.price)}
                </span>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Clock size={16} />
                  <span>{getDurationLabel(plan.duration_days)}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <DollarSign size={16} />
                  <span>
                    {formatCurrency(plan.price / plan.duration_days)}/día
                  </span>
                </div>
                {plan.description && (
                  <p className="text-zinc-500 pt-2 border-t border-zinc-800">
                    {plan.description}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
