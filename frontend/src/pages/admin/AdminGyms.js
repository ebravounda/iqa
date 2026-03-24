import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getGyms, createGym } from '../../lib/api';
import { formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Plus, Building2, Users, Search } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminGyms() {
  const { isSuperAdmin } = useAuth();
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGym, setNewGym] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
    primary_color: '#E1FF01'
  });

  useEffect(() => {
    fetchGyms();
  }, []);

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
    if (!newGym.name) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      await createGym(newGym);
      toast.success('Gimnasio creado exitosamente');
      setShowCreateModal(false);
      setNewGym({ name: '', address: '', phone: '', email: '', primary_color: '#E1FF01' });
      fetchGyms();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear gimnasio');
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
              <Plus size={20} className="mr-2" />
              Nuevo Gimnasio
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Gimnasio</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                <Input
                  value={newGym.name}
                  onChange={(e) => setNewGym({ ...newGym, name: e.target.value })}
                  placeholder="Nombre del gimnasio"
                  className="input-dark"
                  data-testid="gym-name-create-input"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Email</label>
                <Input
                  type="email"
                  value={newGym.email}
                  onChange={(e) => setNewGym({ ...newGym, email: e.target.value })}
                  placeholder="email@gimnasio.com"
                  className="input-dark"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Dirección</label>
                <Input
                  value={newGym.address}
                  onChange={(e) => setNewGym({ ...newGym, address: e.target.value })}
                  placeholder="Dirección del gimnasio"
                  className="input-dark"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Color Principal</label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={newGym.primary_color}
                    onChange={(e) => setNewGym({ ...newGym, primary_color: e.target.value })}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <Input
                    value={newGym.primary_color}
                    onChange={(e) => setNewGym({ ...newGym, primary_color: e.target.value })}
                    className="input-dark font-mono"
                  />
                </div>
              </div>
              <Button onClick={handleCreateGym} className="w-full btn-gym-primary" data-testid="save-gym-btn">
                <Building2 size={20} className="mr-2" />
                Crear Gimnasio
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar gimnasios..."
          className="input-dark pl-10"
        />
      </div>

      {/* Gyms Grid */}
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
            <div key={gym.id} className="stat-card hover:border-zinc-600 transition-colors cursor-pointer">
              <div className="flex items-center gap-4 mb-4">
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl"
                  style={{ backgroundColor: gym.primary_color, color: '#000' }}
                >
                  {gym.name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-bold">{gym.name}</h3>
                  <p className="text-xs text-zinc-500">{gym.email || 'Sin email'}</p>
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                {gym.address && (
                  <p className="text-zinc-400 truncate">{gym.address}</p>
                )}
                <div className="flex justify-between pt-2 border-t border-zinc-800">
                  <span className="text-zinc-500">Creado</span>
                  <span className="text-zinc-400">{formatDate(gym.created_at)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
