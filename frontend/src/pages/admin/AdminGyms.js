import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getGyms, createGym, updateGym } from '../../lib/api';
import { formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { 
  Plus, Building2, Search, MoreVertical, Pencil, Trash2, Ban, CheckCircle,
  AlertTriangle, LogIn, Users, Mail, Shield, CreditCard, Dumbbell, Building, Hotel, Laptop, Save
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { BUSINESS_TYPES } from '../../lib/businessLabels';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminGyms() {
  const { isSuperAdmin, impersonateGym } = useAuth();
  const navigate = useNavigate();
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedGym, setSelectedGym] = useState(null);
  const [impersonating, setImpersonating] = useState(null);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [credentialsForm, setCredentialsForm] = useState({ email: '', password: '' });
  const [credentialsGym, setCredentialsGym] = useState(null);
  const [newGym, setNewGym] = useState({
    name: '', address: '', phone: '', email: '', primary_color: '#E1FF01', max_members: null,
    business_type: 'gym', custom_domain: '', admin_email: '', admin_password: '', admin_name: ''
  });
  const [editGym, setEditGym] = useState({
    name: '', address: '', phone: '', email: '', primary_color: '#E1FF01', max_members: null, business_type: 'gym', custom_domain: ''
  });

  useEffect(() => { fetchGyms(); }, []);

  const fetchGyms = async () => {
    try {
      const response = await getGyms();
      setGyms(response.data);
    } catch (error) {
      toast.error('Error al cargar gimnasios');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGym = async () => {
    if (!newGym.name) { toast.error('El nombre es requerido'); return; }
    if (newGym.admin_email && !newGym.admin_password) { toast.error('Ingresa una contraseña para el administrador'); return; }
    try {
      await createGym(newGym);
      toast.success(newGym.admin_email 
        ? 'Gimnasio creado con administrador' 
        : 'Gimnasio creado exitosamente');
      setShowCreateModal(false);
      setNewGym({ name: '', address: '', phone: '', email: '', primary_color: '#E1FF01', max_members: null, business_type: 'gym', custom_domain: '', admin_email: '', admin_password: '', admin_name: '' });
      fetchGyms();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear gimnasio');
    }
  };

  const handleOpenEdit = (gym) => {
    setSelectedGym(gym);
    setEditGym({
      name: gym.name || '',
      address: gym.address || '',
      phone: gym.phone || '',
      email: gym.email || '',
      primary_color: gym.primary_color || '#E1FF01',
      max_members: gym.max_members || null,
      business_type: gym.business_type || 'gym',
      custom_domain: gym.custom_domain || '',
      auto_approve_members: gym.auto_approve_members || false,
      show_pwa_install_prompt: gym.show_pwa_install_prompt !== false
    });
    setShowEditModal(true);
  };

  const handleUpdateGym = async () => {
    if (!editGym.name) { toast.error('El nombre es requerido'); return; }
    try {
      await updateGym(selectedGym.id, editGym);
      toast.success('Gimnasio actualizado');
      setShowEditModal(false);
      fetchGyms();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleOpenCredentials = (gym) => {
    setCredentialsGym(gym);
    setCredentialsForm({ email: gym.gym_admin_email || '', password: '' });
    setShowCredentialsModal(true);
  };

  const handleUpdateCredentials = async () => {
    if (!credentialsForm.email && !credentialsForm.password) { toast.error('Ingresa un email o contraseña nueva'); return; }
    if (credentialsForm.password && credentialsForm.password.length < 6) { toast.error('La contraseña debe tener al menos 6 caracteres'); return; }
    try {
      const adminId = credentialsGym.admin_id;
      if (!adminId) { toast.error('Este negocio no tiene un administrador asignado'); return; }
      await axios.put(`${API}/auth/admin/${adminId}/credentials`, credentialsForm);
      toast.success('Credenciales actualizadas');
      setShowCredentialsModal(false);
      fetchGyms();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al actualizar credenciales');
    }
  };

  const handleSuspend = async (gym) => {
    try {
      const res = await axios.put(`${API}/gyms/${gym.id}/suspend`);
      toast.success(res.data.status === 'active' ? 'Gimnasio reactivado' : 'Gimnasio suspendido');
      fetchGyms();
    } catch (error) {
      toast.error('Error al cambiar estado');
    }
  };

  const handlePaymentSuspend = async (gym) => {
    const action = gym.status === 'payment_suspended' ? 'reactivar' : 'suspender por falta de pago';
    if (!window.confirm(`¿${gym.status === 'payment_suspended' ? 'Reactivar' : 'Suspender por falta de pago'} "${gym.name}"? ${gym.status !== 'payment_suspended' ? 'El gimnasio y todos sus socios perderán acceso al sistema.' : ''}`)) return;
    try {
      const res = await axios.put(`${API}/gyms/${gym.id}/payment-suspend`);
      toast.success(res.data.message);
      fetchGyms();
    } catch (error) {
      toast.error('Error al cambiar estado');
    }
  };

  const handleDeleteConfirm = (gym) => {
    setSelectedGym(gym);
    setShowDeleteConfirm(true);
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/gyms/${selectedGym.id}`);
      toast.success('Gimnasio eliminado permanentemente');
      setShowDeleteConfirm(false);
      setSelectedGym(null);
      fetchGyms();
    } catch (error) {
      toast.error('Error al eliminar gimnasio');
    }
  };

  const handleImpersonate = async (gym) => {
    setImpersonating(gym.id);
    try {
      await impersonateGym(gym.id);
      toast.success(`Sesión iniciada en ${gym.name}`);
      navigate('/admin');
    } catch (error) {
      toast.error('Error al iniciar sesión en el gimnasio');
    } finally {
      setImpersonating(null);
    }
  };

  const filteredGyms = gyms.filter(g =>
    g.name.toLowerCase().includes(search.toLowerCase()) ||
    (g.gym_admin_email || '').toLowerCase().includes(search.toLowerCase())
  );

  if (!isSuperAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-zinc-500">Solo el Super Admin puede ver esta sección</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-gyms">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Negocios</h1>
          <p className="text-zinc-400 text-sm">{gyms.length} negocios registrados</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-gym-btn">
              <Plus size={20} className="mr-2" /> Nuevo Negocio
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800 max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Crear Nuevo Negocio</DialogTitle></DialogHeader>
            <div className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Nombre del Negocio *</label>
                  <Input value={newGym.name} onChange={(e) => setNewGym({ ...newGym, name: e.target.value })}
                    placeholder="Ej: PowerFit Gym" className="input-dark" data-testid="gym-name-input" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Email del Negocio</label>
                  <Input type="email" value={newGym.email} onChange={(e) => setNewGym({ ...newGym, email: e.target.value })}
                    placeholder="contacto@gimnasio.com" className="input-dark" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Dirección</label>
                    <Input value={newGym.address} onChange={(e) => setNewGym({ ...newGym, address: e.target.value })}
                      placeholder="Dirección" className="input-dark" />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Teléfono</label>
                    <Input value={newGym.phone} onChange={(e) => setNewGym({ ...newGym, phone: e.target.value })}
                      placeholder="Teléfono" className="input-dark" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Capacidad máxima</label>
                    <Input type="number" value={newGym.max_members || ''} onChange={(e) => setNewGym({ ...newGym, max_members: e.target.value ? parseInt(e.target.value) : null })}
                      placeholder="Ej: 500" className="input-dark" />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Color Principal</label>
                    <div className="flex gap-2">
                      <input type="color" value={newGym.primary_color} onChange={(e) => setNewGym({ ...newGym, primary_color: e.target.value })} className="w-10 h-10 rounded cursor-pointer" />
                      <Input value={newGym.primary_color} onChange={(e) => setNewGym({ ...newGym, primary_color: e.target.value })} className="input-dark font-mono" />
                    </div>
                  </div>
                </div>

                {/* Business Type Selector */}
                <div>
                  <label className="text-sm text-zinc-400 mb-2 block">Tipo de Negocio</label>
                  <div className="grid grid-cols-2 gap-2" data-testid="business-type-selector">
                    {BUSINESS_TYPES.map(bt => {
                      const Icon = bt.value === 'gym' ? Dumbbell : bt.value === 'condominium' ? Building : bt.value === 'hotel' ? Hotel : Laptop;
                      const selected = newGym.business_type === bt.value;
                      return (
                        <button key={bt.value} type="button" onClick={() => setNewGym({ ...newGym, business_type: bt.value })}
                          className={`flex items-center gap-2 p-3 rounded-xl text-sm font-medium transition-all border ${selected ? 'border-[var(--gym-primary)] text-white' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}
                          style={selected ? { background: 'rgba(225,255,1,0.1)' } : {}}
                          data-testid={`business-type-${bt.value}`}
                        >
                          <Icon size={18} style={selected ? { color: 'var(--gym-primary)' } : {}} />
                          {bt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Domain */}
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Dominio Personalizado</label>
                  <Input value={newGym.custom_domain} onChange={(e) => setNewGym({ ...newGym, custom_domain: e.target.value.toLowerCase() })} className="input-dark" placeholder="panel.sunegocio.com" data-testid="gym-custom-domain" />
                  <p className="text-[10px] text-zinc-500 mt-1">El negocio debe apuntar un CNAME a app.ingresoqr.com</p>
                </div>

                {/* Admin Credentials Section */}
                <div className="pt-4 border-t border-zinc-800">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield size={16} className="text-blue-400" />
                    <label className="text-sm font-bold text-zinc-300">Credenciales del Administrador</label>
                  </div>
                  <p className="text-xs text-zinc-500 mb-3">
                    Se creara un usuario administrador para este negocio
                  </p>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-zinc-400 mb-1 block">Nombre del Admin</label>
                      <Input value={newGym.admin_name} onChange={(e) => setNewGym({ ...newGym, admin_name: e.target.value })}
                        placeholder="Ej: Juan Pérez" className="input-dark" data-testid="admin-name-input" />
                    </div>
                    <div>
                      <label className="text-sm text-zinc-400 mb-1 block">Email del Admin *</label>
                      <Input type="email" value={newGym.admin_email} onChange={(e) => setNewGym({ ...newGym, admin_email: e.target.value })}
                        placeholder="admin@gimnasio.com" className="input-dark" data-testid="admin-email-input" />
                    </div>
                    <div>
                      <label className="text-sm text-zinc-400 mb-1 block">Contraseña del Admin *</label>
                      <Input type="password" value={newGym.admin_password} onChange={(e) => setNewGym({ ...newGym, admin_password: e.target.value })}
                        placeholder="Mínimo 6 caracteres" className="input-dark" data-testid="admin-password-input" />
                    </div>
                  </div>
                </div>
              </div>
              <Button onClick={handleCreateGym} className="w-full btn-gym-primary mt-6" data-testid="save-gym-btn">
                <Building2 size={20} className="mr-2" /> {BUSINESS_TYPES.find(bt => bt.value === newGym.business_type)?.label ? `Crear ${BUSINESS_TYPES.find(bt => bt.value === newGym.business_type).label}` : 'Crear Negocio'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <Input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por nombre o email admin..." className="input-dark pl-10" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-6 w-32 mb-4" />
              <div className="skeleton h-4 w-24" />
            </div>
          ))
        ) : filteredGyms.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Building2 size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay negocios registrados</p>
          </div>
        ) : (
          filteredGyms.map((gym) => (
            <div key={gym.id} className={`stat-card transition-colors relative ${
              gym.status === 'suspended' ? 'border-red-500/30 opacity-70' 
              : gym.status === 'payment_suspended' ? 'border-orange-500/30 opacity-80' 
              : 'hover:border-zinc-600'
            }`}>
              {gym.status === 'suspended' && (
                <div className="absolute top-3 right-14 px-2 py-0.5 bg-red-500/20 border border-red-500/40 rounded text-red-400 text-xs font-bold" data-testid={`gym-suspended-badge-${gym.id}`}>
                  SUSPENDIDO
                </div>
              )}
              {gym.status === 'payment_suspended' && (
                <div className="absolute top-3 right-14 px-2 py-0.5 bg-orange-500/20 border border-orange-500/40 rounded text-orange-400 text-xs font-bold" data-testid={`gym-payment-suspended-badge-${gym.id}`}>
                  IMPAGO
                </div>
              )}
              
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl shrink-0"
                    style={{ backgroundColor: gym.primary_color, color: '#000' }}>
                    {gym.name.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-bold truncate">{gym.name}</h3>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold" style={{ background: 'var(--bg-tertiary)', color: 'var(--gym-primary)' }} data-testid={`gym-type-badge-${gym.id}`}>
                        {BUSINESS_TYPES.find(bt => bt.value === (gym.business_type || 'gym'))?.label || 'Gimnasio'}
                      </span>
                      {gym.custom_domain && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-blue-500/10 text-blue-400" data-testid={`gym-domain-badge-${gym.id}`}>
                          {gym.custom_domain}
                        </span>
                      )}
                      <p className="text-xs text-zinc-500 truncate">{gym.email || 'Sin email'}</p>
                    </div>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0 shrink-0" data-testid={`gym-actions-${gym.id}`}>
                      <MoreVertical size={16} />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
                    <DropdownMenuItem onClick={() => handleOpenEdit(gym)} className="cursor-pointer" data-testid={`gym-edit-${gym.id}`}>
                      <Pencil size={16} className="mr-2" /> Editar
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleSuspend(gym)} className="cursor-pointer" data-testid={`gym-suspend-${gym.id}`}>
                      {gym.status === 'suspended' ? (
                        <><CheckCircle size={16} className="mr-2 text-green-500" /> Reactivar</>
                      ) : (
                        <><Ban size={16} className="mr-2 text-yellow-500" /> Suspender</>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handlePaymentSuspend(gym)} className="cursor-pointer" data-testid={`gym-payment-suspend-${gym.id}`}>
                      {gym.status === 'payment_suspended' ? (
                        <><CheckCircle size={16} className="mr-2 text-green-500" /> Reactivar (Pago recibido)</>
                      ) : (
                        <><CreditCard size={16} className="mr-2 text-orange-500" /> Suspender por Impago</>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleDeleteConfirm(gym)} className="cursor-pointer text-red-500" data-testid={`gym-delete-${gym.id}`}>
                      <Trash2 size={16} className="mr-2" /> Eliminar
                    </DropdownMenuItem>
                    {gym.admin_id && (
                      <DropdownMenuItem onClick={() => handleOpenCredentials(gym)} className="cursor-pointer" data-testid={`gym-credentials-${gym.id}`}>
                        <Shield size={16} className="mr-2 text-blue-400" /> Cambiar Credenciales
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Admin Info */}
              {gym.gym_admin_email && (
                <div className="flex items-center gap-2 mb-3 p-2 rounded-lg bg-zinc-800/50 text-xs">
                  <Mail size={14} className="text-blue-400 shrink-0" />
                  <span className="text-zinc-400 truncate">{gym.gym_admin_email}</span>
                </div>
              )}
              
              <div className="space-y-2 text-sm">
                {gym.address && <p className="text-zinc-400 truncate">{gym.address}</p>}
                <div className="flex justify-between pt-2 border-t border-zinc-800">
                  <span className="text-zinc-500">Creado</span>
                  <span className="text-zinc-400">{formatDate(gym.created_at)}</span>
                </div>
              </div>

              {/* Login as Gym Admin Button */}
              <Button
                onClick={() => handleImpersonate(gym)}
                disabled={impersonating === gym.id || gym.status === 'suspended'}
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white h-10 rounded-xl font-semibold text-sm"
                data-testid={`impersonate-gym-${gym.id}`}
              >
                {impersonating === gym.id ? (
                  <span className="animate-pulse">Iniciando sesión...</span>
                ) : (
                  <>
                    <LogIn size={16} className="mr-2" />
                    Iniciar sesión como Admin
                  </>
                )}
              </Button>
            </div>
          ))
        )}
      </div>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Editar Negocio</DialogTitle></DialogHeader>
          <div className="mt-4">
            <div className="space-y-4">
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                <Input value={editGym.name} onChange={(e) => setEditGym({ ...editGym, name: e.target.value })}
                  placeholder="Nombre del gimnasio" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                <Input type="email" value={editGym.email} onChange={(e) => setEditGym({ ...editGym, email: e.target.value })}
                  placeholder="email@gimnasio.com" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Dirección</label>
                <Input value={editGym.address} onChange={(e) => setEditGym({ ...editGym, address: e.target.value })}
                  placeholder="Dirección" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Teléfono</label>
                <Input value={editGym.phone} onChange={(e) => setEditGym({ ...editGym, phone: e.target.value })}
                  placeholder="Teléfono" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Capacidad máxima de socios</label>
                <Input type="number" value={editGym.max_members || ''} onChange={(e) => setEditGym({ ...editGym, max_members: e.target.value ? parseInt(e.target.value) : null })}
                  placeholder="Ej: 100, 500, 2000" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Color Principal</label>
                <div className="flex gap-2">
                  <input type="color" value={editGym.primary_color} onChange={(e) => setEditGym({ ...editGym, primary_color: e.target.value })} className="w-10 h-10 rounded cursor-pointer" />
                  <Input value={editGym.primary_color} onChange={(e) => setEditGym({ ...editGym, primary_color: e.target.value })} className="input-dark font-mono" />
                </div>
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-2 block">Tipo de Negocio</label>
                <div className="grid grid-cols-2 gap-2" data-testid="edit-business-type-selector">
                  {BUSINESS_TYPES.map(bt => {
                    const Icon = bt.value === 'gym' ? Dumbbell : bt.value === 'condominium' ? Building : bt.value === 'hotel' ? Hotel : Laptop;
                    const selected = editGym.business_type === bt.value;
                    return (
                      <button key={bt.value} type="button" onClick={() => setEditGym({ ...editGym, business_type: bt.value })}
                        className={`flex items-center gap-2 p-3 rounded-xl text-sm font-medium transition-all border ${selected ? 'border-[var(--gym-primary)] text-white' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}
                        style={selected ? { background: 'rgba(225,255,1,0.1)' } : {}}
                        data-testid={`edit-business-type-${bt.value}`}
                      >
                        <Icon size={18} style={selected ? { color: 'var(--gym-primary)' } : {}} />
                        {bt.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Auto-aprobar nuevos socios</label>
                <div 
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${editGym.auto_approve_members ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-zinc-700 bg-zinc-800/50'}`}
                  onClick={() => setEditGym({ ...editGym, auto_approve_members: !editGym.auto_approve_members })}
                  data-testid="edit-gym-auto-approve"
                >
                  <div className={`w-10 h-6 rounded-full p-0.5 transition-all ${editGym.auto_approve_members ? 'bg-emerald-500' : 'bg-zinc-600'}`}>
                    <div className={`w-5 h-5 rounded-full bg-white transition-all ${editGym.auto_approve_members ? 'translate-x-4' : 'translate-x-0'}`} />
                  </div>
                  <span className={`text-sm ${editGym.auto_approve_members ? 'text-emerald-400' : 'text-zinc-500'}`}>
                    {editGym.auto_approve_members ? 'Activado — Los socios con pago realizado se activan automaticamente' : 'Desactivado — Los socios requieren aprobacion manual'}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Mostrar banner "Instalar App" (PWA)</label>
                <div
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${editGym.show_pwa_install_prompt ? 'border-blue-500/50 bg-blue-500/5' : 'border-zinc-700 bg-zinc-800/50'}`}
                  onClick={() => setEditGym({ ...editGym, show_pwa_install_prompt: !editGym.show_pwa_install_prompt })}
                  data-testid="toggle-pwa-install"
                >
                  <div className={`w-10 h-6 rounded-full p-0.5 transition-all ${editGym.show_pwa_install_prompt ? 'bg-blue-500' : 'bg-zinc-600'}`}>
                    <div className={`w-5 h-5 rounded-full bg-white transition-all ${editGym.show_pwa_install_prompt ? 'translate-x-4' : 'translate-x-0'}`} />
                  </div>
                  <span className={`text-sm ${editGym.show_pwa_install_prompt ? 'text-blue-400' : 'text-zinc-500'}`}>
                    {editGym.show_pwa_install_prompt ? 'Activado — Los socios veran la opcion de instalar la app' : 'Desactivado — No se muestra el banner de instalacion'}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Dominio Personalizado</label>
                <Input value={editGym.custom_domain} onChange={(e) => setEditGym({ ...editGym, custom_domain: e.target.value.toLowerCase() })} className="input-dark" placeholder="panel.sunegocio.com" data-testid="edit-gym-custom-domain" />
                <p className="text-[10px] text-zinc-500 mt-1">CNAME apuntando a app.ingresoqr.com</p>
              </div>
            </div>
            <Button onClick={handleUpdateGym} className="w-full btn-gym-primary mt-4" data-testid="update-gym-btn">
              <Pencil size={20} className="mr-2" /> Guardar Cambios
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <div className="text-center py-4">
            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle size={32} className="text-red-500" />
            </div>
            <h2 className="text-xl font-bold mb-2">Eliminar Negocio</h2>
            <p className="text-zinc-400 mb-2">
              Desea confirmar la eliminacion del negocio?
            </p>
            <p className="text-lg font-bold mb-4" style={{ color: selectedGym?.primary_color }}>
              {selectedGym?.name}
            </p>
            <p className="text-red-400 text-sm mb-6">
              Se eliminarán TODOS los datos: socios, membresías, clases, accesos y configuraciones. Esta acción no se puede deshacer.
            </p>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1 border-zinc-700" onClick={() => setShowDeleteConfirm(false)}
                data-testid="cancel-delete-btn">
                Cancelar
              </Button>
              <Button className="flex-1 bg-red-600 hover:bg-red-700 text-white" onClick={handleDelete}
                data-testid="confirm-delete-btn">
                <Trash2 size={18} className="mr-2" /> Sí, Eliminar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      {/* Credentials Modal */}
      <Dialog open={showCredentialsModal} onOpenChange={setShowCredentialsModal}>
        <DialogContent className="bg-zinc-900 border-zinc-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Shield size={20} className="text-blue-400" />
              Cambiar Credenciales — {credentialsGym?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Nuevo Email</label>
              <Input type="email" value={credentialsForm.email} onChange={e => setCredentialsForm({...credentialsForm, email: e.target.value})}
                placeholder="admin@negocio.com" className="input-dark" data-testid="credentials-email" />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Nueva Contraseña</label>
              <Input type="password" value={credentialsForm.password} onChange={e => setCredentialsForm({...credentialsForm, password: e.target.value})}
                placeholder="Dejar vacio para no cambiar" className="input-dark" data-testid="credentials-password" />
            </div>
            <Button onClick={handleUpdateCredentials} className="w-full btn-gym-primary" data-testid="save-credentials-btn">
              <Save size={16} className="mr-2" /> Guardar Credenciales
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
