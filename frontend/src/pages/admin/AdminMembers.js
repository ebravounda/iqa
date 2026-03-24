import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getMembers, createMember, updateMember, approveMember, blockMember, getPlans, createMembership } from '../../lib/api';
import { formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Search, Plus, MoreVertical, Check, X, 
  UserPlus, CreditCard, Eye, Ban, CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';

export default function AdminMembers() {
  const { admin, isSuperAdmin } = useAuth();
  const [members, setMembers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMembershipModal, setShowMembershipModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [newMember, setNewMember] = useState({ name: '', email: '', phone: '', gym_id: '' });
  const [selectedPlan, setSelectedPlan] = useState('');

  useEffect(() => {
    fetchMembers();
    fetchPlans();
  }, [statusFilter]);

  const fetchMembers = async () => {
    try {
      const gymId = isSuperAdmin ? null : admin?.gym_id;
      const status = statusFilter === 'all' ? null : statusFilter;
      const response = await getMembers(gymId, status);
      setMembers(response.data);
    } catch (error) {
      toast.error('Error al cargar socios');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const gymId = isSuperAdmin ? null : admin?.gym_id;
      const response = await getPlans(gymId);
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching plans:', error);
    }
  };

  const handleCreateMember = async () => {
    if (!newMember.name || !newMember.email) {
      toast.error('Nombre y email son requeridos');
      return;
    }

    try {
      const gymId = isSuperAdmin ? newMember.gym_id : admin?.gym_id;
      await createMember({ ...newMember, gym_id: gymId });
      toast.success('Socio creado exitosamente');
      setShowCreateModal(false);
      setNewMember({ name: '', email: '', phone: '', gym_id: '' });
      fetchMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear socio');
    }
  };

  const handleApprove = async (memberId) => {
    try {
      await approveMember(memberId);
      toast.success('Socio aprobado');
      fetchMembers();
    } catch (error) {
      toast.error('Error al aprobar socio');
    }
  };

  const handleBlock = async (memberId) => {
    try {
      await blockMember(memberId);
      toast.success('Socio bloqueado');
      fetchMembers();
    } catch (error) {
      toast.error('Error al bloquear socio');
    }
  };

  const handleActivate = async (memberId) => {
    try {
      await updateMember(memberId, { status: 'active' });
      toast.success('Socio activado');
      fetchMembers();
    } catch (error) {
      toast.error('Error al activar socio');
    }
  };

  const handleAssignMembership = async () => {
    if (!selectedPlan || !selectedMember) {
      toast.error('Selecciona un plan');
      return;
    }

    try {
      await createMembership({ member_id: selectedMember.id, plan_id: selectedPlan });
      toast.success('Membresía asignada');
      setShowMembershipModal(false);
      setSelectedMember(null);
      setSelectedPlan('');
    } catch (error) {
      toast.error('Error al asignar membresía');
    }
  };

  const filteredMembers = members.filter(m => 
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.email.toLowerCase().includes(search.toLowerCase()) ||
    m.code.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge-success',
      pending: 'badge-warning',
      blocked: 'badge-danger'
    };
    const labels = {
      active: 'Activo',
      pending: 'Pendiente',
      blocked: 'Bloqueado'
    };
    return <span className={`badge ${badges[status]}`}>{labels[status]}</span>;
  };

  return (
    <div className="space-y-6" data-testid="admin-members">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Socios</h1>
          <p className="text-zinc-400 text-sm">{members.length} socios registrados</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-member-btn">
              <Plus size={20} className="mr-2" />
              Nuevo Socio
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Socio</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                <Input
                  value={newMember.name}
                  onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                  placeholder="Nombre completo"
                  className="input-dark"
                  data-testid="member-name-input"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                <Input
                  type="email"
                  value={newMember.email}
                  onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                  placeholder="email@ejemplo.com"
                  className="input-dark"
                  data-testid="member-email-input"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Teléfono (opcional)</label>
                <Input
                  value={newMember.phone}
                  onChange={(e) => setNewMember({ ...newMember, phone: e.target.value })}
                  placeholder="+1 234 567 890"
                  className="input-dark"
                />
              </div>
              <Button onClick={handleCreateMember} className="w-full btn-gym-primary" data-testid="save-member-btn">
                <UserPlus size={20} className="mr-2" />
                Crear Socio
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nombre, email o código..."
            className="input-dark pl-10"
            data-testid="search-members"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-700" data-testid="status-filter">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-700">
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="active">Activos</SelectItem>
            <SelectItem value="pending">Pendientes</SelectItem>
            <SelectItem value="blocked">Bloqueados</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="stat-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Socio</th>
                <th>Código</th>
                <th>Email</th>
                <th>Estado</th>
                <th>Registro</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8">
                    <div className="skeleton h-4 w-32 mx-auto" />
                  </td>
                </tr>
              ) : filteredMembers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-zinc-500 py-8">
                    No se encontraron socios
                  </td>
                </tr>
              ) : (
                filteredMembers.map((member) => (
                  <tr key={member.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center font-bold text-sm">
                          {member.name.charAt(0)}
                        </div>
                        <span className="font-medium">{member.name}</span>
                      </div>
                    </td>
                    <td>
                      <code className="text-sm bg-zinc-800 px-2 py-1 rounded font-mono">
                        {member.code}
                      </code>
                    </td>
                    <td className="text-zinc-400">{member.email}</td>
                    <td>{getStatusBadge(member.status)}</td>
                    <td className="text-zinc-400 text-sm">{formatDate(member.created_at)}</td>
                    <td>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid={`member-actions-${member.code}`}>
                            <MoreVertical size={16} />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
                          <DropdownMenuItem 
                            onClick={() => { setSelectedMember(member); setShowMembershipModal(true); }}
                            className="cursor-pointer"
                          >
                            <CreditCard size={16} className="mr-2" />
                            Asignar Membresía
                          </DropdownMenuItem>
                          {member.status === 'pending' && (
                            <DropdownMenuItem onClick={() => handleApprove(member.id)} className="cursor-pointer text-emerald-500">
                              <CheckCircle size={16} className="mr-2" />
                              Aprobar
                            </DropdownMenuItem>
                          )}
                          {member.status === 'blocked' ? (
                            <DropdownMenuItem onClick={() => handleActivate(member.id)} className="cursor-pointer text-emerald-500">
                              <Check size={16} className="mr-2" />
                              Activar
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => handleBlock(member.id)} className="cursor-pointer text-red-500">
                              <Ban size={16} className="mr-2" />
                              Bloquear
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Membership Modal */}
      <Dialog open={showMembershipModal} onOpenChange={setShowMembershipModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle>Asignar Membresía</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-zinc-400">
              Asignar membresía a <strong>{selectedMember?.name}</strong>
            </p>
            <Select value={selectedPlan} onValueChange={setSelectedPlan}>
              <SelectTrigger className="w-full bg-zinc-800 border-zinc-700" data-testid="plan-select">
                <SelectValue placeholder="Seleccionar plan" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {plans.map((plan) => (
                  <SelectItem key={plan.id} value={plan.id}>
                    {plan.name} - ${plan.price} ({plan.duration_days} días)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleAssignMembership} className="w-full btn-gym-primary" data-testid="assign-membership-btn">
              <CreditCard size={20} className="mr-2" />
              Asignar Membresía
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
