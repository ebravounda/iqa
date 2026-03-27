import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getMembers, createMember, updateMember, approveMember, suspendMember, deleteMember, getPlans, createMembership, checkExpiredMemberships, getGyms, setMemberQRMode, uploadAvatarAdmin, getMemberDevices, deactivateDevice, deactivateAllDevices } from '../../lib/api';
import { formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Search, Plus, MoreVertical, Check,
  UserPlus, CreditCard, Pencil, Trash2, Ban, CheckCircle,
  AlertTriangle, RefreshCw, PauseCircle, Banknote, Receipt, QrCode, Camera,
  Mail, Phone, Copy, X as XIcon, Smartphone
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { MemberAvatar } from '../../components/MemberAvatar';

function MemberContactPopover({ member, onClose }) {
  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copiado`);
  };

  return (
    <div className="absolute right-0 top-full mt-1 z-50 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl shadow-black/40 p-3 min-w-[260px] animate-in fade-in slide-in-from-top-1 duration-150"
      data-testid={`contact-popover-${member.code}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Contacto</span>
        <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300 transition-colors">
          <XIcon size={14} />
        </button>
      </div>
      {member.email && (
        <div className="flex items-center gap-2 group">
          <Mail size={13} className="text-zinc-500 shrink-0" />
          <span className="text-sm text-zinc-300 truncate flex-1">{member.email}</span>
          <button onClick={() => copyToClipboard(member.email, 'Email')} 
            className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-[var(--gym-primary)] transition-all" title="Copiar">
            <Copy size={13} />
          </button>
        </div>
      )}
      {member.phone && (
        <div className="flex items-center gap-2 group mt-1.5">
          <Phone size={13} className="text-zinc-500 shrink-0" />
          <span className="text-sm text-zinc-300 truncate flex-1">{member.phone}</span>
          <button onClick={() => copyToClipboard(member.phone, 'Teléfono')} 
            className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-[var(--gym-primary)] transition-all" title="Copiar">
            <Copy size={13} />
          </button>
        </div>
      )}
      {!member.email && !member.phone && (
        <p className="text-xs text-zinc-500 italic">Sin datos de contacto</p>
      )}
    </div>
  );
}

export default function AdminMembers() {
  const { admin, isSuperAdmin, hasPermission } = useAuth();
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
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [suspendReason, setSuspendReason] = useState('');
  const [newMember, setNewMember] = useState({ name: '', email: '', phone: '', gym_id: admin?.gym_id || '', gender: 'prefer_not_to_say' });
  const [editData, setEditData] = useState({ name: '', email: '', phone: '', can_bring_guests: false, max_guests_per_month: 2, guest_valid_days: 1 });
  const [expandedContact, setExpandedContact] = useState(null);
  const [showDevicesModal, setShowDevicesModal] = useState(false);
  const [devicesMember, setDevicesMember] = useState(null);
  const [memberDevices, setMemberDevices] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [gyms, setGyms] = useState([]);

  useEffect(() => { fetchMembers(); fetchPlans(); if (isSuperAdmin) fetchGyms(); }, [statusFilter]);

  const fetchGyms = async () => {
    try { const res = await getGyms(); setGyms(res.data); if (res.data.length > 0 && !newMember.gym_id) setNewMember(prev => ({ ...prev, gym_id: res.data[0].id })); }
    catch (error) { console.error('Error fetching gyms:', error); }
  };

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
    setEditData({ name: member.name, email: member.email || '', phone: member.phone || '', can_bring_guests: member.can_bring_guests || false, max_guests_per_month: member.max_guests_per_month || 2, guest_valid_days: member.guest_valid_days || 1 });
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

  const handleOpenPayment = (member) => {
    setSelectedMember(member);
    setSelectedPlan('');
    setPaymentMethod('cash');
    setPaymentNotes('');
    setShowPaymentModal(true);
  };

  const handleManualPayment = async () => {
    if (!selectedPlan) { toast.error('Selecciona un plan'); return; }
    const plan = plans.find(p => p.id === selectedPlan);
    if (!plan) return;
    try {
      const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;
      await fetch(`${API_URL}/payments/manual`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          member_id: selectedMember.id,
          plan_id: selectedPlan,
          payment_method: paymentMethod,
          amount: plan.price,
          notes: paymentNotes || null
        })
      }).then(r => r.json());
      toast.success('Pago registrado y membresía activada');
      setShowPaymentModal(false);
      fetchMembers();
    } catch (error) { toast.error('Error al registrar pago'); }
  };

  useEffect(() => {
    if (!expandedContact) return;
    const handler = (e) => {
      if (!e.target.closest(`[data-testid="contact-popover-${members.find(m => m.id === expandedContact)?.code}"]`) &&
          !e.target.closest(`[data-testid^="contact-btn-"]`)) {
        setExpandedContact(null);
      }
    };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [expandedContact, members]);

  const handleOpenDevices = async (member) => {
    setDevicesMember(member);
    setShowDevicesModal(true);
    try {
      const res = await getMemberDevices(member.id);
      setMemberDevices(res.data);
    } catch { setMemberDevices([]); }
  };

  const handleDeactivateDevice = async (deviceId) => {
    try {
      await deactivateDevice(deviceId);
      toast.success('Dispositivo desactivado');
      const res = await getMemberDevices(devicesMember.id);
      setMemberDevices(res.data);
    } catch { toast.error('Error al desactivar'); }
  };

  const handleDeactivateAll = async () => {
    if (!devicesMember) return;
    try {
      await deactivateAllDevices(devicesMember.id);
      toast.success('Todos los dispositivos desactivados');
      const res = await getMemberDevices(devicesMember.id);
      setMemberDevices(res.data);
    } catch { toast.error('Error'); }
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
                {isSuperAdmin && (
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Gimnasio</label>
                    <Select value={newMember.gym_id} onValueChange={(v) => setNewMember({ ...newMember, gym_id: v })}>
                      <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="member-gym-select">
                        <SelectValue placeholder="Seleccionar gimnasio" />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-zinc-700">
                        {gyms.map((g) => (
                          <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
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
                  <label className="text-sm text-zinc-400 mb-1 block">Telefono (opcional)</label>
                  <Input value={newMember.phone} onChange={(e) => setNewMember({ ...newMember, phone: e.target.value })}
                    placeholder="+1 234 567 890" className="input-dark" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Sexo</label>
                  <select className="input-gym w-full" value={newMember.gender} onChange={e => setNewMember({ ...newMember, gender: e.target.value })} data-testid="member-gender-select">
                    <option value="male">Hombre</option>
                    <option value="female">Mujer</option>
                    <option value="prefer_not_to_say">Prefiero no contestar</option>
                  </select>
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
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left p-3 text-zinc-400 font-medium text-xs uppercase tracking-wider">Socio</th>
              <th className="text-left p-3 text-zinc-400 font-medium text-xs uppercase tracking-wider">Código</th>
              <th className="text-center p-3 text-zinc-400 font-medium text-xs uppercase tracking-wider">Estado</th>
              <th className="text-center p-3 text-zinc-400 font-medium text-xs uppercase tracking-wider w-[100px]">Contacto</th>
              <th className="text-right p-3 w-[50px]"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="text-center py-8"><div className="skeleton h-4 w-32 mx-auto" /></td></tr>
            ) : filteredMembers.length === 0 ? (
              <tr><td colSpan={5} className="text-center text-zinc-500 py-8">No se encontraron socios</td></tr>
            ) : (
              filteredMembers.map((member) => (
                <tr key={member.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 transition-colors group">
                  <td className="p-3">
                    <div className="flex items-center gap-3">
                      <MemberAvatar member={member} size={36} />
                      <div className="min-w-0">
                        <span className="font-medium text-white block truncate">{member.name}</span>
                        {member.status === 'suspended' && member.suspension_reason && (
                          <p className="text-[11px] text-orange-400 truncate max-w-[200px]" data-testid={`member-suspend-reason-${member.code}`}>
                            {member.suspension_reason}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <code className="text-xs bg-zinc-800 px-2 py-0.5 rounded font-mono text-zinc-300">{member.code}</code>
                      {member.qr_mode === 'static' && <span className="text-[10px] bg-cyan-900/30 text-cyan-400 px-1.5 py-0.5 rounded leading-none">QR Fijo</span>}
                    </div>
                  </td>
                  <td className="p-3 text-center">{getStatusBadge(member.status)}</td>
                  <td className="p-3 text-center relative">
                    <button
                      onClick={(e) => { e.stopPropagation(); setExpandedContact(expandedContact === member.id ? null : member.id); }}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-all border border-zinc-700/50 hover:border-zinc-600"
                      data-testid={`contact-btn-${member.code}`}
                    >
                      <Mail size={12} />
                      <span className="hidden sm:inline">Ver</span>
                    </button>
                    {expandedContact === member.id && (
                      <MemberContactPopover member={member} onClose={() => setExpandedContact(null)} />
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-60 group-hover:opacity-100 transition-opacity" data-testid={`member-actions-${member.code}`}>
                          <MoreVertical size={16} />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
                        {hasPermission('members_edit') && (
                          <DropdownMenuItem onClick={() => handleOpenEdit(member)} className="cursor-pointer" data-testid={`member-edit-${member.code}`}>
                            <Pencil size={16} className="mr-2" /> Editar
                          </DropdownMenuItem>
                        )}
                        {hasPermission('payments_register') && (
                          <DropdownMenuItem onClick={() => { setSelectedMember(member); setShowMembershipModal(true); }} className="cursor-pointer">
                            <CreditCard size={16} className="mr-2" /> Asignar Membresía
                          </DropdownMenuItem>
                        )}
                        {hasPermission('payments_register') && (
                          <DropdownMenuItem onClick={() => handleOpenPayment(member)} className="cursor-pointer text-emerald-400" data-testid={`member-payment-${member.code}`}>
                            <Banknote size={16} className="mr-2" /> Registrar Pago
                          </DropdownMenuItem>
                        )}
                        {member.status === 'pending' && hasPermission('members_edit') && (
                          <DropdownMenuItem onClick={() => handleApprove(member.id)} className="cursor-pointer text-emerald-500">
                            <CheckCircle size={16} className="mr-2" /> Aprobar
                          </DropdownMenuItem>
                        )}
                        {hasPermission('members_suspend') && (
                          <>
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
                          </>
                        )}
                        {hasPermission('members_delete') && (
                          <DropdownMenuItem onClick={() => handleOpenDelete(member)} className="cursor-pointer text-red-500" data-testid={`member-delete-${member.code}`}>
                            <Trash2 size={16} className="mr-2" /> Eliminar
                          </DropdownMenuItem>
                        )}
                        {isSuperAdmin && (
                          <>
                            <DropdownMenuSeparator className="bg-zinc-700" />
                            <DropdownMenuItem onClick={async () => {
                              const newMode = member.qr_mode === 'static' ? 'dynamic' : 'static';
                              try { await setMemberQRMode(member.id, newMode); toast.success(`QR ${newMode === 'static' ? 'estatico' : 'dinamico'} asignado`); fetchMembers(); }
                              catch (e) { toast.error('Error'); }
                            }} className="cursor-pointer text-cyan-400" data-testid={`member-qr-${member.code}`}>
                              <QrCode size={16} className="mr-2" /> {member.qr_mode === 'static' ? 'Cambiar a QR Dinamico' : 'Asignar QR Estatico'}
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuSeparator className="bg-zinc-700" />
                        <DropdownMenuItem className="cursor-pointer text-violet-400 p-0" data-testid={`member-photo-${member.code}`}>
                          <label className="flex items-center gap-2 cursor-pointer w-full px-2 py-1.5">
                            <Camera size={16} /> Subir Foto
                            <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={async (e) => {
                              const file = e.target.files[0];
                              if (!file) return;
                              if (file.size > 2 * 1024 * 1024) { toast.error('La imagen no puede superar 2MB'); return; }
                              try { await uploadAvatarAdmin(member.id, file); toast.success('Foto actualizada'); fetchMembers(); }
                              catch (err) { toast.error(err.response?.data?.detail || 'Error al subir foto'); }
                            }} />
                          </label>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleOpenDevices(member)} className="cursor-pointer text-zinc-400" data-testid={`member-devices-${member.code}`}>
                          <Smartphone size={16} className="mr-2" /> Dispositivos
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
            {/* Guest Config */}
            <div className="border-t border-zinc-800 pt-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={editData.can_bring_guests} onChange={(e) => setEditData({ ...editData, can_bring_guests: e.target.checked })} className="w-4 h-4 rounded" data-testid="edit-guest-toggle" />
                <span className="text-sm">Puede traer invitados</span>
              </label>
              {editData.can_bring_guests && (
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div>
                    <label className="text-xs text-zinc-500 mb-1 block">Max invitados/mes</label>
                    <Input type="number" min="1" max="10" value={editData.max_guests_per_month} onChange={(e) => setEditData({ ...editData, max_guests_per_month: parseInt(e.target.value) || 2 })} className="input-dark" data-testid="edit-max-guests" />
                  </div>
                  <div>
                    <label className="text-xs text-zinc-500 mb-1 block">Dias validez invitacion</label>
                    <Input type="number" min="1" max="30" value={editData.guest_valid_days} onChange={(e) => setEditData({ ...editData, guest_valid_days: parseInt(e.target.value) || 1 })} className="input-dark" data-testid="edit-guest-days" />
                  </div>
                </div>
              )}
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

      {/* Manual Payment Modal */}
      <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader><DialogTitle>Registrar Pago</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="flex items-center gap-3 p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
              <Receipt size={24} className="text-emerald-400 shrink-0" />
              <div>
                <p className="font-medium">{selectedMember?.name}</p>
                <p className="text-sm text-zinc-400">Código: {selectedMember?.code}</p>
              </div>
            </div>
            
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Plan</label>
              <Select value={selectedPlan} onValueChange={setSelectedPlan}>
                <SelectTrigger className="w-full bg-zinc-800 border-zinc-700" data-testid="payment-plan-select">
                  <SelectValue placeholder="Seleccionar plan" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-700">
                  {plans.map((plan) => (
                    <SelectItem key={plan.id} value={plan.id}>{plan.name} - ${plan.price} ({plan.duration_days} días)</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Método de Pago</label>
              <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                <SelectTrigger className="w-full bg-zinc-800 border-zinc-700" data-testid="payment-method-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-700">
                  <SelectItem value="cash">Efectivo</SelectItem>
                  <SelectItem value="card_reception">Tarjeta en Recepción</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Notas (opcional)</label>
              <Input value={paymentNotes} onChange={(e) => setPaymentNotes(e.target.value)}
                placeholder="Ej: Pago parcial, descuento aplicado..."
                className="input-dark" data-testid="payment-notes-input" />
            </div>
            
            {selectedPlan && (
              <div className="p-4 bg-zinc-800 rounded-lg text-center">
                <p className="text-sm text-zinc-400">Total a cobrar</p>
                <p className="text-3xl font-black" style={{ color: 'var(--gym-primary)' }}>
                  ${plans.find(p => p.id === selectedPlan)?.price?.toFixed(2) || '0.00'}
                </p>
              </div>
            )}
            
            <Button onClick={handleManualPayment} className="w-full btn-gym-primary" data-testid="confirm-payment-btn">
              <Banknote size={20} className="mr-2" /> Registrar Pago y Activar Membresía
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Devices Modal */}
      <Dialog open={showDevicesModal} onOpenChange={setShowDevicesModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Smartphone size={20} className="text-blue-400" />
              Dispositivos de {devicesMember?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-2 space-y-3">
            {memberDevices.length === 0 ? (
              <p className="text-zinc-500 text-sm text-center py-4">No hay dispositivos registrados</p>
            ) : (
              <>
                <div className="flex items-center justify-between text-xs text-zinc-500">
                  <span>{memberDevices.filter(d => d.active).length} activos / {memberDevices.length} total</span>
                  {memberDevices.some(d => d.active) && (
                    <button onClick={handleDeactivateAll} className="text-red-400 hover:text-red-300 underline" data-testid="deactivate-all-devices">
                      Desactivar todos
                    </button>
                  )}
                </div>
                {memberDevices.map(d => (
                  <div key={d.id} className={`flex items-center gap-3 p-3 rounded-lg border ${d.active ? 'bg-zinc-800/50 border-zinc-700' : 'bg-zinc-900 border-zinc-800 opacity-50'}`}>
                    <Smartphone size={20} className={d.active ? 'text-blue-400' : 'text-zinc-600'} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{d.device_name}</p>
                      <p className="text-[11px] text-zinc-500 truncate">{d.user_agent?.substring(0, 50)}...</p>
                      <p className="text-[10px] text-zinc-600">{d.active ? `Ultimo uso: ${d.last_active?.substring(0, 10)}` : 'Desactivado'}</p>
                    </div>
                    {d.active && (
                      <button onClick={() => handleDeactivateDevice(d.id)}
                        className="text-xs text-red-400 hover:text-red-300 px-2 py-1 border border-red-500/20 rounded hover:bg-red-500/10 transition-colors"
                        data-testid={`deactivate-device-${d.id}`}>
                        Desactivar
                      </button>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
