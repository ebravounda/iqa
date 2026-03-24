import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getGyms, createGym, updateGym } from '../../lib/api';
import { formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { 
  Plus, Building2, Search, MoreVertical, Pencil, Trash2, Ban, CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminGyms() {
  const { isSuperAdmin } = useAuth();
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedGym, setSelectedGym] = useState(null);
  const [newGym, setNewGym] = useState({
    name: '', address: '', phone: '', email: '', primary_color: '#E1FF01', max_members: null
  });
  const [editGym, setEditGym] = useState({
    name: '', address: '', phone: '', email: '', primary_color: '#E1FF01', max_members: null
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
    try {
      await createGym(newGym);
      toast.success('Gimnasio creado exitosamente');
      setShowCreateModal(false);
      setNewGym({ name: '', address: '', phone: '', email: '', primary_color: '#E1FF01', max_members: null });
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
      max_members: gym.max_members || null
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

  const handleSuspend = async (gym) => {
    try {
      const res = await axios.put(`${API}/gyms/${gym.id}/suspend`);
      toast.success(res.data.status === 'suspended' ? 'Gimnasio suspendido' : 'Gimnasio reactivado');
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

  const filteredGyms = gyms.filter(g =>
    g.name.toLowerCase().includes(search.toLowerCase())
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
          <h1 className="text-2xl font-black tracking-tight">Gimnasios</h1>
          <p className="text-zinc-400 text-sm">{gyms.length} gimnasios registrados</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-gym-btn">
              <Plus size={20} className="mr-2" /> Nuevo Gimnasio
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader><DialogTitle>Crear Nuevo Gimnasio</DialogTitle></DialogHeader>
            <div className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                  <Input value={newGym.name} onChange={(e) => setNewGym({ ...newGym, name: e.target.value })}
                    placeholder="Nombre del gimnasio" className="input-dark" data-testid="gym-name-input" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                  <Input type="email" value={newGym.email} onChange={(e) => setNewGym({ ...newGym, email: e.target.value })}
                    placeholder="email@gimnasio.com" className="input-dark" />
                </div>
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
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Capacidad máxima de socios</label>
                  <Input type="number" value={newGym.max_members || ''} onChange={(e) => setNewGym({ ...newGym, max_members: e.target.value ? parseInt(e.target.value) : null })}
                    placeholder="Ej: 100, 500, 2000" className="input-dark" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Color Principal</label>
                  <div className="flex gap-2">
                    <input type="color" value={newGym.primary_color} onChange={(e) => setNewGym({ ...newGym, primary_color: e.target.value })} className="w-10 h-10 rounded cursor-pointer" />
                    <Input value={newGym.primary_color} onChange={(e) => setNewGym({ ...newGym, primary_color: e.target.value })} className="input-dark font-mono" />
                  </div>
                </div>
              </div>
              <Button onClick={handleCreateGym} className="w-full btn-gym-primary mt-4" data-testid="save-gym-btn">
                <Building2 size={20} className="mr-2" /> Crear Gimnasio
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <Input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar gimnasios..." className="input-dark pl-10" />
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
            <p className="text-zinc-500">No hay gimnasios registrados</p>
          </div>
        ) : (
          filteredGyms.map((gym) => (
            <div key={gym.id} className={`stat-card transition-colors relative ${
              gym.status === 'suspended' ? 'border-red-500/30 opacity-70' : 'hover:border-zinc-600'
            }`}>
              {gym.status === 'suspended' && (
                <div className="absolute top-3 right-14 px-2 py-0.5 bg-red-500/20 border border-red-500/40 rounded text-red-400 text-xs font-bold" data-testid={`gym-suspended-badge-${gym.id}`}>
                  GYM SUSPENDIDO
                </div>
              )}
              
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl"
                    style={{ backgroundColor: gym.primary_color, color: '#000' }}>
                    {gym.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold">{gym.name}</h3>
                    <p className="text-xs text-zinc-500">{gym.email || 'Sin email'}</p>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid={`gym-actions-${gym.id}`}>
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
                    <DropdownMenuItem onClick={() => handleDeleteConfirm(gym)} className="cursor-pointer text-red-500" data-testid={`gym-delete-${gym.id}`}>
                      <Trash2 size={16} className="mr-2" /> Eliminar
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              
              <div className="space-y-2 text-sm">
                {gym.address && <p className="text-zinc-400 truncate">{gym.address}</p>}
                <div className="flex justify-between pt-2 border-t border-zinc-800">
                  <span className="text-zinc-500">Creado</span>
                  <span className="text-zinc-400">{formatDate(gym.created_at)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader><DialogTitle>Editar Gimnasio</DialogTitle></DialogHeader>
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
            <h2 className="text-xl font-bold mb-2">Eliminar Gimnasio</h2>
            <p className="text-zinc-400 mb-2">
              ¿Desea confirmar la eliminación del gimnasio?
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
    </div>
  );
}
