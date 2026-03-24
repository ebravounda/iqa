import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { 
  Plus, Calendar, Clock, Users, User, Trash2, Edit, MoreVertical
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DAYS_OF_WEEK = [
  { value: 0, label: 'Lunes' },
  { value: 1, label: 'Martes' },
  { value: 2, label: 'Miércoles' },
  { value: 3, label: 'Jueves' },
  { value: 4, label: 'Viernes' },
  { value: 5, label: 'Sábado' },
  { value: 6, label: 'Domingo' },
];

export default function AdminClasses() {
  const { admin, isSuperAdmin } = useAuth();
  const [classes, setClasses] = useState([]);
  const [trainers, setTrainers] = useState([]);
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedGymId, setSelectedGymId] = useState(admin?.gym_id || '');
  const [newClass, setNewClass] = useState({
    name: '',
    description: '',
    trainer_id: '',
    max_capacity: 20,
    duration_minutes: 60,
    class_type: 'group',
    recurring: false,
    days_of_week: [],
    start_time: '09:00',
    single_date: '',
    single_start_time: '09:00'
  });

  useEffect(() => {
    fetchClasses();
    fetchTrainers();
    if (isSuperAdmin) fetchGyms();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API}/classes`);
      setClasses(response.data);
    } catch (error) {
      toast.error('Error al cargar clases');
    } finally {
      setLoading(false);
    }
  };

  const fetchTrainers = async () => {
    try {
      const response = await axios.get(`${API}/trainers`);
      setTrainers(response.data);
    } catch (error) {
      console.error('Error fetching trainers:', error);
    }
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

  const handleCreateClass = async () => {
    if (!newClass.name) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      const gymId = admin?.gym_id || selectedGymId;
      if (!gymId) {
        toast.error('Selecciona un gimnasio');
        return;
      }
      const payload = {
        ...newClass,
        gym_id: gymId,
        max_capacity: parseInt(newClass.max_capacity),
        duration_minutes: parseInt(newClass.duration_minutes),
        trainer_id: newClass.trainer_id || null
      };

      await axios.post(`${API}/classes`, payload);
      toast.success('Clase creada exitosamente');
      setShowCreateModal(false);
      setNewClass({
        name: '',
        description: '',
        trainer_id: '',
        max_capacity: 20,
        duration_minutes: 60,
        class_type: 'group',
        recurring: false,
        days_of_week: [],
        start_time: '09:00',
        single_date: '',
        single_start_time: '09:00'
      });
      fetchClasses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear clase');
    }
  };

  const handleDeleteClass = async (classId) => {
    if (!window.confirm('¿Estás seguro de eliminar esta clase?')) return;
    
    try {
      await axios.delete(`${API}/classes/${classId}`);
      toast.success('Clase eliminada');
      fetchClasses();
    } catch (error) {
      toast.error('Error al eliminar clase');
    }
  };

  const toggleDay = (dayValue) => {
    setNewClass(prev => {
      const days = prev.days_of_week.includes(dayValue)
        ? prev.days_of_week.filter(d => d !== dayValue)
        : [...prev.days_of_week, dayValue];
      return { ...prev, days_of_week: days };
    });
  };

  return (
    <div className="space-y-6" data-testid="admin-classes">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Clases</h1>
          <p className="text-zinc-400 text-sm">{classes.length} clases activas</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-class-btn">
              <Plus size={20} className="mr-2" />
              Nueva Clase
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Crear Nueva Clase</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {isSuperAdmin && (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Gimnasio</label>
                  <Select value={selectedGymId} onValueChange={setSelectedGymId}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="class-gym-select">
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
                <label className="text-sm text-zinc-400 mb-1 block">Nombre de la Clase</label>
                <Input
                  value={newClass.name}
                  onChange={(e) => setNewClass({ ...newClass, name: e.target.value })}
                  placeholder="Ej: Spinning, Yoga, CrossFit"
                  className="input-dark"
                  data-testid="class-name-input"
                />
              </div>
              
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Descripción</label>
                <Input
                  value={newClass.description}
                  onChange={(e) => setNewClass({ ...newClass, description: e.target.value })}
                  placeholder="Descripción de la clase"
                  className="input-dark"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Entrenador</label>
                  <Select value={newClass.trainer_id || "none"} onValueChange={(v) => setNewClass({ ...newClass, trainer_id: v === "none" ? "" : v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="none">Sin asignar</SelectItem>
                      {trainers.map((t) => (
                        <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Tipo</label>
                  <Select value={newClass.class_type} onValueChange={(v) => setNewClass({ ...newClass, class_type: v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="group">Grupal</SelectItem>
                      <SelectItem value="personal">Personal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Capacidad Máxima</label>
                  <Input
                    type="number"
                    value={newClass.max_capacity}
                    onChange={(e) => setNewClass({ ...newClass, max_capacity: e.target.value })}
                    className="input-dark"
                  />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Duración (min)</label>
                  <Input
                    type="number"
                    value={newClass.duration_minutes}
                    onChange={(e) => setNewClass({ ...newClass, duration_minutes: e.target.value })}
                    className="input-dark"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 py-2">
                <Checkbox 
                  id="recurring"
                  checked={newClass.recurring}
                  onCheckedChange={(checked) => setNewClass({ ...newClass, recurring: checked })}
                />
                <label htmlFor="recurring" className="text-sm cursor-pointer">
                  Clase recurrente (semanal)
                </label>
              </div>

              {newClass.recurring ? (
                <>
                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Días de la semana</label>
                    <div className="flex flex-wrap gap-2">
                      {DAYS_OF_WEEK.map((day) => (
                        <button
                          key={day.value}
                          type="button"
                          onClick={() => toggleDay(day.value)}
                          className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                            newClass.days_of_week.includes(day.value)
                              ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/10 text-[var(--gym-primary)]'
                              : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                          }`}
                        >
                          {day.label.slice(0, 3)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Hora de inicio</label>
                    <Input
                      type="time"
                      value={newClass.start_time}
                      onChange={(e) => setNewClass({ ...newClass, start_time: e.target.value })}
                      className="input-dark"
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Fecha</label>
                    <Input
                      type="date"
                      value={newClass.single_date}
                      onChange={(e) => setNewClass({ ...newClass, single_date: e.target.value })}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Hora de inicio</label>
                    <Input
                      type="time"
                      value={newClass.single_start_time}
                      onChange={(e) => setNewClass({ ...newClass, single_start_time: e.target.value })}
                      className="input-dark"
                    />
                  </div>
                </>
              )}

              <Button onClick={handleCreateClass} className="w-full btn-gym-primary" data-testid="save-class-btn">
                <Calendar size={20} className="mr-2" />
                Crear Clase
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Classes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-6 w-32 mb-4" />
              <div className="skeleton h-4 w-24" />
            </div>
          ))
        ) : classes.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Calendar size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay clases creadas</p>
            <p className="text-zinc-600 text-sm">Crea tu primera clase</p>
          </div>
        ) : (
          classes.map((cls) => (
            <div key={cls.id} className="stat-card relative group">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="absolute top-4 right-4 h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                  >
                    <MoreVertical size={16} />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
                  <DropdownMenuItem onClick={() => handleDeleteClass(cls.id)} className="cursor-pointer text-red-500">
                    <Trash2 size={16} className="mr-2" />
                    Eliminar
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              
              <div className="flex items-center gap-3 mb-4">
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
                >
                  <Calendar size={24} />
                </div>
                <div>
                  <h3 className="font-bold">{cls.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    cls.class_type === 'group' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'
                  }`}>
                    {cls.class_type === 'group' ? 'Grupal' : 'Personal'}
                  </span>
                </div>
              </div>

              {cls.description && (
                <p className="text-zinc-400 text-sm mb-4 line-clamp-2">{cls.description}</p>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Clock size={16} />
                  <span>{cls.duration_minutes} minutos</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <Users size={16} />
                  <span>Máx. {cls.max_capacity} personas</span>
                </div>
                {cls.trainer && (
                  <div className="flex items-center gap-2 text-zinc-400">
                    <User size={16} />
                    <span>{cls.trainer.name}</span>
                  </div>
                )}
                {cls.recurring && cls.days_of_week && (
                  <div className="flex items-center gap-2 text-zinc-400">
                    <Calendar size={16} />
                    <span>
                      {cls.days_of_week.map(d => DAYS_OF_WEEK.find(day => day.value === d)?.label.slice(0, 3)).join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
