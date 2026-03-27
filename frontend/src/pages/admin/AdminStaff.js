import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Plus, User, Mail, Phone, Dumbbell, MoreVertical, Shield, Settings2, Check, X as XIcon
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ROLE_LABELS = {
  'gym_admin': { label: 'Administrador', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  'gym_manager': { label: 'Gestor', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  'trainer': { label: 'Entrenador', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' }
};

const PERMISSION_LABELS = {
  "members_view": "Ver socios",
  "members_create": "Crear socios",
  "members_edit": "Editar socios",
  "members_delete": "Eliminar socios",
  "members_suspend": "Suspender / Reactivar socios",
  "payments_register": "Registrar pagos",
  "pos_sell": "Ventas TPV",
  "pos_products": "Gestionar productos TPV",
  "access_view": "Ver accesos",
  "classes_manage": "Gestionar clases y horarios",
  "data_export": "Exportar datos (Excel)",
  "notifications_send": "Enviar notificaciones",
};

const PERMISSION_GROUPS = [
  { label: 'Socios', permissions: ['members_view', 'members_create', 'members_edit', 'members_suspend', 'members_delete'] },
  { label: 'Pagos y Ventas', permissions: ['payments_register', 'pos_sell', 'pos_products'] },
  { label: 'Operaciones', permissions: ['access_view', 'classes_manage', 'notifications_send', 'data_export'] },
];

const DANGER_PERMISSIONS = ['members_delete', 'members_suspend', 'data_export'];

export default function AdminStaff() {
  const { admin, isSuperAdmin } = useAuth();
  const [staff, setStaff] = useState([]);
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPermsModal, setShowPermsModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [editingPerms, setEditingPerms] = useState([]);
  const [savingPerms, setSavingPerms] = useState(false);
  const [createType, setCreateType] = useState('staff');
  const [selectedGymId, setSelectedGymId] = useState(admin?.gym_id || '');
  const [formData, setFormData] = useState({
    name: '', email: '', password: '', phone: '',
    role: 'gym_manager', specialties: '', bio: ''
  });

  useEffect(() => {
    fetchStaff();
    if (isSuperAdmin) fetchGyms();
  }, []);

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff`);
      setStaff(response.data);
    } catch (error) {
      toast.error('Error al cargar personal');
    } finally { setLoading(false); }
  };

  const fetchGyms = async () => {
    try {
      const response = await axios.get(`${API}/gyms`);
      setGyms(response.data);
      if (response.data.length > 0 && !selectedGymId) {
        setSelectedGymId(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching gyms:', error);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.email || !formData.password) {
      toast.error('Nombre, email y contrasena son requeridos'); return;
    }
    const gymId = admin?.gym_id || selectedGymId;
    if (!gymId) { toast.error('Selecciona un gimnasio'); return; }
    try {
      if (createType === 'trainer') {
        await axios.post(`${API}/trainers`, {
          gym_id: gymId, name: formData.name, email: formData.email,
          password: formData.password, phone: formData.phone || null,
          specialties: formData.specialties ? formData.specialties.split(',').map(s => s.trim()) : [],
          bio: formData.bio || null
        });
      } else {
        await axios.post(`${API}/staff`, {
          gym_id: gymId, name: formData.name, email: formData.email,
          password: formData.password, role: formData.role
        });
      }
      toast.success('Usuario creado exitosamente');
      setShowCreateModal(false);
      setFormData({ name: '', email: '', password: '', phone: '', role: 'gym_manager', specialties: '', bio: '' });
      fetchStaff();
    } catch (error) { toast.error(error.response?.data?.detail || 'Error al crear usuario'); }
  };

  const handleToggleActive = async (userId, currentActive) => {
    if (userId === admin?.id) {
      toast.error('No puedes desactivar tu propia cuenta');
      return;
    }
    try {
      await axios.put(`${API}/staff/${userId}/toggle-active`, { active: !currentActive });
      toast.success(currentActive ? 'Usuario desactivado' : 'Usuario activado');
      fetchStaff();
    } catch (error) { toast.error(error.response?.data?.detail || 'Error al actualizar'); }
  };

  const openPermissions = (user) => {
    setSelectedUser(user);
    setEditingPerms(user.permissions || [
      "members_view", "members_create", "members_edit",
      "payments_register", "pos_sell", "access_view", "classes_manage"
    ]);
    setShowPermsModal(true);
  };

  const togglePerm = (perm) => {
    setEditingPerms(prev => prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]);
  };

  const savePermissions = async () => {
    setSavingPerms(true);
    try {
      await axios.put(`${API}/staff/${selectedUser.id}/permissions`, { permissions: editingPerms });
      toast.success('Permisos actualizados');
      setShowPermsModal(false);
      fetchStaff();
    } catch (error) { toast.error(error.response?.data?.detail || 'Error al guardar permisos'); }
    finally { setSavingPerms(false); }
  };

  const admins = staff.filter(s => s.role === 'gym_admin');
  const managers = staff.filter(s => s.role === 'gym_manager');
  const trainers = staff.filter(s => s.role === 'trainer');

  return (
    <div className="space-y-6" data-testid="admin-staff">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Personal y Entrenadores</h1>
          <p className="text-zinc-400 text-sm">{staff.length} usuarios registrados</p>
        </div>
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-staff-btn">
              <Plus size={20} className="mr-2" /> Agregar Usuario
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
            <DialogHeader><DialogTitle>Agregar Usuario</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-4">
              {isSuperAdmin && (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Gimnasio</label>
                  <Select value={selectedGymId} onValueChange={setSelectedGymId}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="staff-gym-select">
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
              <div className="flex gap-2">
                <button onClick={() => setCreateType('staff')}
                  className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${createType === 'staff' ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/10 text-[var(--gym-primary)]' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}>
                  <Shield size={20} className="mx-auto mb-1" /> Admin/Gestor
                </button>
                <button onClick={() => setCreateType('trainer')}
                  className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${createType === 'trainer' ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/10 text-[var(--gym-primary)]' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}>
                  <Dumbbell size={20} className="mx-auto mb-1" /> Entrenador
                </button>
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Nombre completo" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                <Input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="email@ejemplo.com" className="input-dark" />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Contraseña</label>
                <Input type="password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} placeholder="********" className="input-dark" />
              </div>
              {createType === 'staff' ? (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Rol</label>
                  <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700"><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="gym_admin">Administrador (control total)</SelectItem>
                      <SelectItem value="gym_manager">Gestor (permisos configurables)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-zinc-500 mt-1">
                    {formData.role === 'gym_admin' ? 'Control total sobre el gimnasio' : 'Permisos configurables por el administrador'}
                  </p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Teléfono</label>
                    <Input value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} placeholder="+1 234 567 890" className="input-dark" />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Especialidades (separadas por coma)</label>
                    <Input value={formData.specialties} onChange={(e) => setFormData({ ...formData, specialties: e.target.value })} placeholder="Yoga, Pilates, Spinning" className="input-dark" />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Biografía</label>
                    <Input value={formData.bio} onChange={(e) => setFormData({ ...formData, bio: e.target.value })} placeholder="Breve descripción..." className="input-dark" />
                  </div>
                </>
              )}
              <Button onClick={handleCreate} className="w-full btn-gym-primary"><Plus size={20} className="mr-2" /> Crear Usuario</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Admins */}
      {admins.length > 0 && (
        <StaffSection title="Administradores" icon={<Shield size={20} className="text-purple-400" />}
          users={admins} onToggleActive={handleToggleActive} currentAdminId={admin?.id} />
      )}

      {/* Managers with permissions */}
      <div>
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <User size={20} className="text-blue-400" /> Gestores
        </h2>
        {managers.length === 0 ? (
          <div className="stat-card text-center py-8">
            <User size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay gestores registrados</p>
            <p className="text-zinc-600 text-xs mt-1">Los gestores son personal de recepcion con permisos limitados</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {managers.map((user) => (
              <ManagerCard key={user.id} user={user} onToggleActive={handleToggleActive} onEditPerms={openPermissions} currentAdminId={admin?.id} />
            ))}
          </div>
        )}
      </div>

      {/* Trainers */}
      <StaffSection title="Entrenadores" icon={<Dumbbell size={20} className="text-emerald-400" />}
        users={trainers} onToggleActive={handleToggleActive} isTrainer emptyMsg="No hay entrenadores registrados" currentAdminId={admin?.id} />

      {/* Permissions Modal */}
      <Dialog open={showPermsModal} onOpenChange={setShowPermsModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings2 size={20} className="text-blue-400" />
              Permisos de {selectedUser?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-2 space-y-5">
            <p className="text-xs text-zinc-500">Activa o desactiva los permisos de este gestor. Los cambios se aplican inmediatamente al guardar.</p>
            
            {PERMISSION_GROUPS.map((group) => (
              <div key={group.label}>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">{group.label}</h4>
                <div className="space-y-1">
                  {group.permissions.map((perm) => {
                    const active = editingPerms.includes(perm);
                    const isDanger = DANGER_PERMISSIONS.includes(perm);
                    return (
                      <button
                        key={perm}
                        onClick={() => togglePerm(perm)}
                        className={`w-full flex items-center justify-between p-2.5 rounded-lg border transition-all text-left ${
                          active
                            ? isDanger
                              ? 'border-red-500/30 bg-red-500/5'
                              : 'border-[var(--gym-primary)]/30 bg-[var(--gym-primary)]/5'
                            : 'border-zinc-800 bg-zinc-900 hover:border-zinc-700'
                        }`}
                        data-testid={`perm-toggle-${perm}`}
                      >
                        <span className={`text-sm ${active ? (isDanger ? 'text-red-300' : 'text-white') : 'text-zinc-500'}`}>
                          {PERMISSION_LABELS[perm]}
                        </span>
                        <div className={`w-5 h-5 rounded-md flex items-center justify-center transition-colors ${
                          active
                            ? isDanger
                              ? 'bg-red-500 text-white'
                              : 'bg-[var(--gym-primary)] text-black'
                            : 'bg-zinc-800 border border-zinc-700'
                        }`}>
                          {active && <Check size={12} strokeWidth={3} />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
            
            <div className="pt-2 flex gap-3">
              <Button variant="outline" className="flex-1 border-zinc-700" onClick={() => setShowPermsModal(false)}>
                Cancelar
              </Button>
              <Button onClick={savePermissions} disabled={savingPerms} className="flex-1 btn-gym-primary" data-testid="save-permissions-btn">
                {savingPerms ? 'Guardando...' : 'Guardar Permisos'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function StaffSection({ title, icon, users, onToggleActive, isTrainer = false, emptyMsg, currentAdminId }) {
  if (users.length === 0 && emptyMsg) {
    return (
      <div>
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">{icon} {title}</h2>
        <div className="stat-card text-center py-8">
          <Dumbbell size={48} className="mx-auto text-zinc-600 mb-4" />
          <p className="text-zinc-500">{emptyMsg}</p>
        </div>
      </div>
    );
  }
  if (users.length === 0) return null;
  return (
    <div>
      <h2 className="text-lg font-bold mb-4 flex items-center gap-2">{icon} {title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {users.map((user) => (
          <UserCard key={user.id} user={user} onToggleActive={onToggleActive} isTrainer={isTrainer} currentAdminId={currentAdminId} />
        ))}
      </div>
    </div>
  );
}

function ManagerCard({ user, onToggleActive, onEditPerms, currentAdminId }) {
  const roleInfo = ROLE_LABELS[user.role];
  const permCount = (user.permissions || []).length;
  const totalPerms = Object.keys(PERMISSION_LABELS).length;

  return (
    <div className={`stat-card ${user.active === false ? 'opacity-60' : ''}`} data-testid={`staff-card-${user.id}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center font-bold text-lg text-blue-400">
            {user.name?.charAt(0)}
          </div>
          <div>
            <h3 className="font-bold text-white">{user.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${roleInfo.color}`}>{roleInfo.label}</span>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0"><MoreVertical size={16} /></Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
            <DropdownMenuItem onClick={() => onEditPerms(user)} className="cursor-pointer" data-testid={`edit-perms-${user.id}`}>
              <Settings2 size={16} className="mr-2" /> Permisos
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-zinc-700" />
            {user.id !== currentAdminId && (
              <DropdownMenuItem onClick={() => onToggleActive(user.id, user.active !== false)} className="cursor-pointer text-red-400">
                {user.active === false ? 'Activar' : 'Desactivar'}
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-zinc-400">
          <Mail size={14} /> <span className="truncate">{user.email}</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-zinc-800">
        <button onClick={() => onEditPerms(user)}
          className="w-full flex items-center justify-between p-2 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition-colors group"
          data-testid={`perms-btn-${user.id}`}>
          <span className="text-xs text-zinc-400 group-hover:text-zinc-300">
            <Settings2 size={12} className="inline mr-1.5" />
            {permCount}/{totalPerms} permisos activos
          </span>
          <div className="flex gap-0.5">
            {Array.from({ length: totalPerms }, (_, i) => (
              <div key={i} className={`w-1.5 h-3 rounded-sm ${i < permCount ? 'bg-[var(--gym-primary)]' : 'bg-zinc-700'}`} />
            ))}
          </div>
        </button>
      </div>
    </div>
  );
}

function UserCard({ user, onToggleActive, isTrainer = false, currentAdminId }) {
  const roleInfo = ROLE_LABELS[user.role] || { label: user.role, color: 'bg-zinc-700 text-zinc-300' };
  return (
    <div className={`stat-card ${user.active === false ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-zinc-700 flex items-center justify-center font-bold text-lg">
            {user.name?.charAt(0)}
          </div>
          <div>
            <h3 className="font-bold">{user.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${roleInfo.color}`}>{roleInfo.label}</span>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0"><MoreVertical size={16} /></Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
            {user.id !== currentAdminId ? (
              <DropdownMenuItem onClick={() => onToggleActive(user.id, user.active !== false)} className="cursor-pointer text-red-400">
                {user.active === false ? 'Activar' : 'Desactivar'}
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem disabled className="text-zinc-600 cursor-not-allowed">
                Tu cuenta
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-zinc-400"><Mail size={14} /> <span className="truncate">{user.email}</span></div>
        {user.phone && <div className="flex items-center gap-2 text-zinc-400"><Phone size={14} /> <span>{user.phone}</span></div>}
        {isTrainer && user.specialties?.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-2">
            {user.specialties.map((s, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{s}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
