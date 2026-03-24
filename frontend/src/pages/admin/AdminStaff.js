import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Plus, User, Mail, Phone, Dumbbell, Trash2, MoreVertical, Shield
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ROLE_LABELS = {
  'gym_admin': { label: 'Administrador', color: 'bg-purple-500/10 text-purple-400' },
  'gym_manager': { label: 'Gestor', color: 'bg-blue-500/10 text-blue-400' },
  'trainer': { label: 'Entrenador', color: 'bg-emerald-500/10 text-emerald-400' }
};

export default function AdminStaff() {
  const { admin, isSuperAdmin } = useAuth();
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createType, setCreateType] = useState('staff'); // 'staff' or 'trainer'
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    role: 'gym_manager',
    specialties: '',
    bio: ''
  });

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff`);
      setStaff(response.data);
    } catch (error) {
      toast.error('Error al cargar personal');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.email || !formData.password) {
      toast.error('Nombre, email y contraseña son requeridos');
      return;
    }

    try {
      if (createType === 'trainer') {
        await axios.post(`${API}/trainers`, {
          gym_id: admin?.gym_id,
          name: formData.name,
          email: formData.email,
          password: formData.password,
          phone: formData.phone || null,
          specialties: formData.specialties ? formData.specialties.split(',').map(s => s.trim()) : [],
          bio: formData.bio || null
        });
      } else {
        await axios.post(`${API}/staff`, {
          gym_id: admin?.gym_id,
          name: formData.name,
          email: formData.email,
          password: formData.password,
          role: formData.role
        });
      }
      
      toast.success('Usuario creado exitosamente');
      setShowCreateModal(false);
      setFormData({
        name: '',
        email: '',
        password: '',
        phone: '',
        role: 'gym_manager',
        specialties: '',
        bio: ''
      });
      fetchStaff();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear usuario');
    }
  };

  const handleToggleActive = async (userId, currentActive) => {
    try {
      await axios.put(`${API}/trainers/${userId}`, { active: !currentActive });
      toast.success(currentActive ? 'Usuario desactivado' : 'Usuario activado');
      fetchStaff();
    } catch (error) {
      toast.error('Error al actualizar');
    }
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
              <Plus size={20} className="mr-2" />
              Agregar Usuario
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
            <DialogHeader>
              <DialogTitle>Agregar Usuario</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {/* Type Selection */}
              <div className="flex gap-2">
                <button
                  onClick={() => setCreateType('staff')}
                  className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                    createType === 'staff'
                      ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/10 text-[var(--gym-primary)]'
                      : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                  }`}
                >
                  <Shield size={20} className="mx-auto mb-1" />
                  Admin/Gestor
                </button>
                <button
                  onClick={() => setCreateType('trainer')}
                  className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                    createType === 'trainer'
                      ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/10 text-[var(--gym-primary)]'
                      : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                  }`}
                >
                  <Dumbbell size={20} className="mx-auto mb-1" />
                  Entrenador
                </button>
              </div>

              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Nombre completo"
                  className="input-dark"
                />
              </div>

              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@ejemplo.com"
                  className="input-dark"
                />
              </div>

              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Contraseña</label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="••••••••"
                  className="input-dark"
                />
              </div>

              {createType === 'staff' ? (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Rol</label>
                  <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="gym_admin">Administrador (control total)</SelectItem>
                      <SelectItem value="gym_manager">Gestor (sin configuración)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-zinc-500 mt-1">
                    {formData.role === 'gym_admin' 
                      ? 'Puede gestionar todo: socios, clases, configuración, personal'
                      : 'Puede gestionar socios y clases, pero no configuración ni personal'
                    }
                  </p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Teléfono</label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+1 234 567 890"
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Especialidades (separadas por coma)</label>
                    <Input
                      value={formData.specialties}
                      onChange={(e) => setFormData({ ...formData, specialties: e.target.value })}
                      placeholder="Yoga, Pilates, Spinning"
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Biografía</label>
                    <Input
                      value={formData.bio}
                      onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                      placeholder="Breve descripción..."
                      className="input-dark"
                    />
                  </div>
                </>
              )}

              <Button onClick={handleCreate} className="w-full btn-gym-primary">
                <Plus size={20} className="mr-2" />
                Crear Usuario
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Admins Section */}
      {admins.length > 0 && (
        <div>
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Shield size={20} className="text-purple-400" />
            Administradores
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {admins.map((user) => (
              <UserCard key={user.id} user={user} onToggleActive={handleToggleActive} />
            ))}
          </div>
        </div>
      )}

      {/* Managers Section */}
      {managers.length > 0 && (
        <div>
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <User size={20} className="text-blue-400" />
            Gestores
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {managers.map((user) => (
              <UserCard key={user.id} user={user} onToggleActive={handleToggleActive} />
            ))}
          </div>
        </div>
      )}

      {/* Trainers Section */}
      <div>
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Dumbbell size={20} className="text-emerald-400" />
          Entrenadores
        </h2>
        {trainers.length === 0 ? (
          <div className="stat-card text-center py-8">
            <Dumbbell size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay entrenadores registrados</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trainers.map((user) => (
              <UserCard key={user.id} user={user} onToggleActive={handleToggleActive} isTrainer />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function UserCard({ user, onToggleActive, isTrainer = false }) {
  const roleInfo = ROLE_LABELS[user.role] || { label: user.role, color: 'bg-zinc-700 text-zinc-300' };
  
  return (
    <div className={`stat-card ${user.active === false ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {user.avatar_url ? (
            <img src={user.avatar_url} alt={user.name} className="w-12 h-12 rounded-xl object-cover" />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-zinc-700 flex items-center justify-center font-bold text-lg">
              {user.name?.charAt(0)}
            </div>
          )}
          <div>
            <h3 className="font-bold">{user.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${roleInfo.color}`}>
              {roleInfo.label}
            </span>
          </div>
        </div>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreVertical size={16} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
            <DropdownMenuItem 
              onClick={() => onToggleActive(user.id, user.active !== false)}
              className="cursor-pointer"
            >
              {user.active === false ? 'Activar' : 'Desactivar'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-zinc-400">
          <Mail size={14} />
          <span className="truncate">{user.email}</span>
        </div>
        {user.phone && (
          <div className="flex items-center gap-2 text-zinc-400">
            <Phone size={14} />
            <span>{user.phone}</span>
          </div>
        )}
        {isTrainer && user.specialties?.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-2">
            {user.specialties.map((s, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">
                {s}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
