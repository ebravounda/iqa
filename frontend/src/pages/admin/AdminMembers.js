import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getMembers, createMember, updateMember, approveMember, suspendMember, deleteMember, getPlans, createMembership, checkExpiredMemberships } from '../../lib/api';
import { formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Search, Plus, MoreVertical, Check,
  UserPlus, CreditCard, Pencil, Trash2, Ban, CheckCircle,
  AlertTriangle, RefreshCw, PauseCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';

export default function AdminMembers() {
  const { admin, isSuperAdmin } = useAuth();
  const [members, setMembers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showSuspendModal, setShowSuspendModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showMembershipModal, setShowMembershipModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [suspendReason, setSuspendReason] = useState('');
  const [newMember, setNewMember] = useState({ name: '', email: '', phone: '', gym_id: '' });
  const [editData, setEditData] = useState({ name: '', email: '', phone: '' });
  const [selectedPlan, setSelectedPlan] = useState('');

  useEffect(() => { fetchMembers(); fetchPlans(); }, [statusFilter]);

  const fetchMembers = async () => {
    try {
      const gymId = isSuperAdmin ? null : admin?.gym_id;
      const status = statusFilter === 'all' ? null : statusFilter;
      const response = await getMembers(gymId, status);
      setMembers(response.data);
    } catch (error) {
      toast.error('Error al cargar socios');
    } finally { setLoading(false); }
  };

  const fetchPlans = async () => {
    try {
      const gymId = isSuperAdmin ? null : admin?.gym_id;
      const response = await getPlans(gymId);
      setPlans(response.data);
    } catch (error) { console.error('Error fetching plans:', error); }
  };

  const handleCreateMember = async () => {
    if (!newMember.name || !newMember.email) { toast.error('Nombre y email son requeridos'); return; }
    try {
      const gymId = isSuperAdmin ? newMember.gym_id : admin?.gym_id;
      await createMember({ ...newMember, gym_id: gymId });
      toast.success('Socio creado exitosamente');
      setShowCreateModal(false);
      setNewMember({ name: '', email: '', phone: '', gym_id: '' });
      fetchMembers();
    } catch (error) { toast.error(error.response?.data?.detail || 'Error al crear socio'); }
  };

  const handleOpenEdit = (member) => {
    setSelectedMember(member);
    setEditData({ name: member.name, email: member.email || '', phone: member.phone || '' });
    setShowEditModal(true);
  };

  const handleUpdateMember = async () => {
    if (!editData.name) { toast.error('El nombre es requerido'); return; }
    try {
      await updateMember(selectedMember.id, editData);
      toast.success('Socio actualizado');
      setShowEditModal(false);
      fetchMembers();
    } catch (error) { toast.error('Error al actualizar'); }
  };

  const handleApprove = async (memberId) => {
    try { await approveMember(memberId); toast.success('Socio aprobado'); fetchMembers(); }
    catch (error) { toast.error('Error al aprobar socio'); }
  };

  const handleActivate = async (memberId) => {
    try { await updateMember(memberId, { status: 'active', suspension_reason: null }); toast.success('Socio activado'); fetchMembers(); }
    catch (error) { toast.error('Error al activar socio'); }
  };

  const handleOpenSuspend = (member) => {
    setSelectedMember(member);
    setSuspendReason('');
    setShowSuspendModal(true);
  };

  const handleSuspend = async () => {
    if (!suspendReason.trim()) { toast.error('Indica el motivo de la suspensión'); return; }
    try {
      await suspendMember(selectedMember.id, suspendReason);
      toast.success('Socio suspendido');
      setShowSuspendModal(false);
      fetchMembers();
    } catch (error) { toast.error('Error al suspender'); }
  };

  const handleOpenDelete = (member) => {
    setSelectedMember(member);
    setShowDeleteConfirm(true);
  };

  const handleDelete = async () => {
    try {
      await deleteMember(selectedMember.id);
      toast.success('Socio eliminado permanentemente');
      setShowDeleteConfirm(false);
      fetchMembers();
    } catch (error) { toast.error('Error al eliminar'); }
  };

  const handleCheckExpired = async () => {
    try {
      const res = await checkExpiredMemberships();
      toast.success(res.data.message);
      fetchMembers();
    } catch (error) { toast.error('Error al verificar'); }
  };

  const filteredMembers = members.filter(m =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.email.toLowerCase().includes(search.toLowerCase()) ||
    m.code.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const badges = { active: 'badge-success', pending: 'badge-warning', blocked: 'badge-danger', suspended: 'bg-orange-500/20 text-orange-400 border border-orange-500/30' };
    const labels = { active: 'Activo', pending: 'Pendiente', blocked: 'Bloqueado', suspended: 'Suspendido' };
    return <span className={`badge ${badges[status] || 'badge-warning'}`}>{labels[status] || status}</span>;
  };

  return (
    <div className="space-y-6" data-testid="admin-members">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Socios</h1>
          <p className="text-zinc-400 text-sm">{members.length} socios registrados</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-zinc-700 text-zinc-300" onClick={handleCheckExpired}
            data-testid="check-expired-btn" title="Suspender socios con membresía vencida">
            <RefreshCw size={16} className="mr-2" /> Verificar Vencidos
          </Button>
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button className="btn-gym-primary" data-testid="create-member-btn">
                <Plus size={20} className="mr-2" /> Nuevo Socio
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-zinc-800">
              <DialogHeader><DialogTitle>Crear Nuevo Socio</DialogTitle></DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                  <Input value={newMember.name} onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                    placeholder="Nombre completo" className="input-dark" data-testid="member-name-input" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                  <Input type="email" value={newMember.email} onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                    placeholder="email@ejemplo.com" className="input-dark" data-testid="member-email-input" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Teléfono (opcional)</label>
                  <Input value={newMember.phone} onChange={(e) => setNewMember({ ...newMember, phone: e.target.value })}
                    placeholder="+1 234 567 890" className="input-dark" />
                </div>
                <Button onClick={handleCreateMember} className="w-full btn-gym-primary" data-testid="save-member-btn">
                  <UserPlus size={20} className="mr-2" /> Crear Socio
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <Input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nombre, email o código..." className="input-dark pl-10" data-testid="search-members" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-700" data-testid="status-filter">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-700">
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="active">Activos</SelectItem>
            <SelectItem value="pending">Pendientes</SelectItem>
            <SelectItem value="suspended">Suspendidos</SelectItem>
            <SelectItem value="blocked">Bloqueados</SelectItem>
          </SelectContent>
        </Select>
      </div>

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
                <tr><td colSpan={6} className="text-center py-8"><div className="skeleton h-4 w-32 mx-auto" /></td></tr>
              ) : filteredMembers.length === 0 ? (
                <tr><td colSpan={6} className="text-center text-zinc-500 py-8">No se encontraron socios</td></tr>
              ) : (
                filteredMembers.map((member) => (
                  <tr key={member.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center font-bold text-sm">
                          {member.name.charAt(0)}
                        </div>
                        <div>
                          <span className="font-medium">{member.name}</span>
                          {member.status === 'suspended' && member.suspension_reason && (
                            <p className="text-xs text-orange-400 mt-0.5" data-testid={`member-suspend-reason-${member.code}`}>
                              {member.suspension_reason}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td><code className="text-sm bg-zinc-800 px-2 py-1 rounded font-mono">{member.code}</code></td>
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
                          <DropdownMenuItem onClick={() => handleOpenEdit(member)} className="cursor-pointer" data-testid={`member-edit-${member.code}`}>
                            <Pencil size={16} className="mr-2" /> Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => { setSelectedMember(member); setShowMembershipModal(true); }} className="cursor-pointer">
                            <CreditCard size={16} className="mr-2" /> Asignar Membresía
                          </DropdownMenuItem>
                          {member.status === 'pending' && (
                            <DropdownMenuItem onClick={() => handleApprove(member.id)} className="cursor-pointer text-emerald-500">
                              <CheckCircle size={16} className="mr-2" /> Aprobar
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator className="bg-zinc-700" />
                          {(member.status === 'suspended' || member.status === 'blocked') ? (
                            <DropdownMenuItem onClick={() => handleActivate(member.id)} className="cursor-pointer text-emerald-500" data-testid={`member-activate-${member.code}`}>
                              <Check size={16} className="mr-2" /> Reactivar
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => handleOpenSuspend(member)} className="cursor-pointer text-orange-400" data-testid={`member-suspend-${member.code}`}>
                              <PauseCircle size={16} className="mr-2" /> Suspender
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => handleOpenDelete(member)} className="cursor-pointer text-red-500" data-testid={`member-delete-${member.code}`}>
                            <Trash2 size={16} className="mr-2" /> Eliminar
                          </DropdownMenuItem>
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
          <DialogHeader><DialogTitle>Asignar Membresía</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-zinc-400">Asignar membresía a <strong>{selectedMember?.name}</strong></p>
            <Select value={selectedPlan} onValueChange={setSelectedPlan}>
              <SelectTrigger className="w-full bg-zinc-800 border-zinc-700" data-testid="plan-select">
                <SelectValue placeholder="Seleccionar plan" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {plans.map((plan) => (
                  <SelectItem key={plan.id} value={plan.id}>{plan.name} - ${plan.price} ({plan.duration_days} días)</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={async () => {
              if (!selectedPlan || !selectedMember) { toast.error('Selecciona un plan'); return; }
              try { await createMembership({ member_id: selectedMember.id, plan_id: selectedPlan }); toast.success('Membresía asignada'); setShowMembershipModal(false); setSelectedPlan(''); }
              catch (error) { toast.error('Error al asignar membresía'); }
            }} className="w-full btn-gym-primary" data-testid="assign-membership-btn">
              <CreditCard size={20} className="mr-2" /> Asignar Membresía
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader><DialogTitle>Editar Socio</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
              <Input value={editData.name} onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                className="input-dark" data-testid="edit-member-name" />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Email</label>
              <Input type="email" value={editData.email} onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                className="input-dark" data-testid="edit-member-email" />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Teléfono</label>
              <Input value={editData.phone} onChange={(e) => setEditData({ ...editData, phone: e.target.value })}
                className="input-dark" />
            </div>
            <Button onClick={handleUpdateMember} className="w-full btn-gym-primary" data-testid="update-member-btn">
              <Pencil size={20} className="mr-2" /> Guardar Cambios
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Suspend Modal */}
      <Dialog open={showSuspendModal} onOpenChange={setShowSuspendModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <DialogHeader><DialogTitle>Suspender Socio</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="flex items-center gap-3 p-3 bg-orange-500/10 rounded-lg border border-orange-500/20">
              <PauseCircle size={24} className="text-orange-400 shrink-0" />
              <div>
                <p className="font-medium">{selectedMember?.name}</p>
                <p className="text-sm text-zinc-400">Código: {selectedMember?.code}</p>
              </div>
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Motivo de la suspensión *</label>
              <Textarea value={suspendReason} onChange={(e) => setSuspendReason(e.target.value)}
                placeholder="Ej: Falta de pago, conducta inapropiada, solicitud del socio..."
                className="bg-zinc-800 border-zinc-700 min-h-[100px]" data-testid="suspend-reason-input" />
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1 border-zinc-700" onClick={() => setShowSuspendModal(false)}>Cancelar</Button>
              <Button className="flex-1 bg-orange-600 hover:bg-orange-700 text-white" onClick={handleSuspend} data-testid="confirm-suspend-btn">
                <Ban size={18} className="mr-2" /> Suspender
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <div className="text-center py-4">
            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle size={32} className="text-red-500" />
            </div>
            <h2 className="text-xl font-bold mb-2">Eliminar Socio</h2>
            <p className="text-zinc-400 mb-2">¿Desea confirmar la eliminación del socio?</p>
            <p className="text-lg font-bold text-white mb-2">{selectedMember?.name}</p>
            <p className="text-sm text-zinc-500 mb-4">Código: {selectedMember?.code}</p>
            <p className="text-red-400 text-sm mb-6">Se eliminarán TODOS sus datos: membresías, reservas, accesos e invitados. Esta acción no se puede deshacer.</p>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1 border-zinc-700" onClick={() => setShowDeleteConfirm(false)} data-testid="cancel-delete-member-btn">Cancelar</Button>
              <Button className="flex-1 bg-red-600 hover:bg-red-700 text-white" onClick={handleDelete} data-testid="confirm-delete-member-btn">
                <Trash2 size={18} className="mr-2" /> Sí, Eliminar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
