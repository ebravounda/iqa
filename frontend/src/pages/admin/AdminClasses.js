import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useBusiness } from '../../context/BusinessContext';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { 
  Plus, Calendar, Clock, Users, User, Trash2, Edit, MoreVertical
} from 'lucide-react';
import { toast } from 'sonner';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DAYS_OF_WEEK = [
  { value: 0, label: 'Lunes' },
  { value: 1, label: 'Martes' },
  { value: 2, label: 'Miercoles' },
  { value: 3, label: 'Jueves' },
  { value: 4, label: 'Viernes' },
  { value: 5, label: 'Sabado' },
  { value: 6, label: 'Domingo' },
];

const defaultClass = {
  name: '', description: '', trainer_id: '', max_capacity: 20, duration_minutes: 60,
  class_type: 'group', recurring: false, days_of_week: [], start_time: '09:00',
  end_time: '10:00', start_date: '', end_date: '', single_date: '', single_start_time: '09:00'
};

export default function AdminClasses() {
  const { admin, isSuperAdmin } = useAuth();
  const { labels } = useBusiness();
  const [classes, setClasses] = useState([]);
  const [trainers, setTrainers] = useState([]);
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedGymId, setSelectedGymId] = useState(admin?.gym_id || '');
  const [editClass, setEditClass] = useState(null);
  const [formData, setFormData] = useState({ ...defaultClass });

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

  const handleSaveClass = async () => {
    if (!formData.name) { toast.error('El nombre es requerido'); return; }
    try {
      const gymId = admin?.gym_id || selectedGymId;
      if (!gymId) { toast.error('Selecciona un gimnasio'); return; }
      const payload = {
        ...formData, gym_id: gymId,
        max_capacity: parseInt(formData.max_capacity),
        duration_minutes: parseInt(formData.duration_minutes),
        trainer_id: formData.trainer_id || null
      };
      if (editClass) {
        await axios.put(`${API}/classes/${editClass.id}`, payload);
        toast.success('Clase actualizada');
      } else {
        await axios.post(`${API}/classes`, payload);
        toast.success('Clase creada exitosamente');
      }
      closeModal();
      fetchClasses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar clase');
    }
  };

  const openCreate = () => {
    setEditClass(null);
    setFormData({ ...defaultClass });
    setShowModal(true);
  };

  const openEdit = (cls) => {
    setEditClass(cls);
    setFormData({
      name: cls.name || '', description: cls.description || '', trainer_id: cls.trainer_id || '',
      max_capacity: cls.max_capacity || 20, duration_minutes: cls.duration_minutes || 60,
      class_type: cls.class_type || 'group', recurring: cls.recurring || false,
      days_of_week: cls.days_of_week || [], start_time: cls.start_time || '09:00',
      end_time: cls.end_time || '10:00', start_date: cls.start_date || '', end_date: cls.end_date || '',
      single_date: cls.single_date || '', single_start_time: cls.single_start_time || '09:00'
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditClass(null);
    setFormData({ ...defaultClass });
  };

  const handleDeleteClass = async (classId) => {
    if (!window.confirm('Eliminar esta clase y todos sus horarios?')) return;
    try {
      await axios.delete(`${API}/classes/${classId}`);
      toast.success('Clase eliminada');
      fetchClasses();
    } catch (error) {
      toast.error('Error al eliminar clase');
    }
  };

  const handleCleanupSchedules = async () => {
    try {
      const res = await axios.post(`${API}/classes/cleanup-stale-schedules`);
      const d = res.data;
      toast.success(`Limpieza completada: ${d.total_removed} horarios eliminados`);
    } catch (error) {
      toast.error('Error al limpiar horarios');
    }
  };

  const toggleDay = (dayValue) => {
    setFormData(prev => {
      const days = prev.days_of_week.includes(dayValue)
        ? prev.days_of_week.filter(d => d !== dayValue)
        : [...prev.days_of_week, dayValue];
      return { ...prev, days_of_week: days };
    });
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6" data-testid="admin-classes">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">{labels.classes}</h1>
          <p className="text-zinc-400 text-sm">{classes.length} {labels.classes.toLowerCase()} activas</p>
        </div>
        
        <div className="flex gap-2">
          <Button onClick={handleCleanupSchedules} variant="outline" className="border-zinc-700 text-zinc-400 hover:text-white" data-testid="cleanup-schedules-btn">
            <Trash2 size={16} className="mr-2" />
            Limpiar Horarios
          </Button>
          <Button onClick={openCreate} className="btn-gym-primary" data-testid="create-class-btn">
            <Plus size={20} className="mr-2" />
            Nueva Clase
          </Button>
        </div>
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={showModal} onOpenChange={(open) => { if (!open) closeModal(); }}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle data-testid="class-modal-title">
              {editClass ? 'Editar Clase' : 'Crear Nueva Clase'}
            </DialogTitle>
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
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                placeholder="Ej: Spinning, Yoga, CrossFit"
                className="input-dark"
                data-testid="class-name-input"
              />
            </div>
            
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Descripcion</label>
              <Input
                value={formData.description}
                onChange={(e) => updateField('description', e.target.value)}
                placeholder="Descripcion de la clase"
                className="input-dark"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Entrenador</label>
                <Select value={formData.trainer_id || "none"} onValueChange={(v) => updateField('trainer_id', v === "none" ? "" : v)}>
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
                <Select value={formData.class_type} onValueChange={(v) => updateField('class_type', v)}>
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
                <label className="text-sm text-zinc-400 mb-1 block">Capacidad Maxima</label>
                <Input
                  type="number"
                  value={formData.max_capacity}
                  onChange={(e) => updateField('max_capacity', e.target.value)}
                  className="input-dark"
                  data-testid="class-capacity-input"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Duracion (min)</label>
                <Input
                  type="number"
                  value={formData.duration_minutes}
                  onChange={(e) => updateField('duration_minutes', e.target.value)}
                  className="input-dark"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 py-2">
              <Checkbox 
                id="recurring"
                checked={formData.recurring}
                onCheckedChange={(checked) => updateField('recurring', checked)}
              />
              <label htmlFor="recurring" className="text-sm cursor-pointer">
                Clase recurrente (semanal)
              </label>
            </div>

            {formData.recurring ? (
              <>
                <div>
                  <label className="text-sm text-zinc-400 mb-2 block">Dias de la semana</label>
                  <div className="flex flex-wrap gap-2">
                    {DAYS_OF_WEEK.map((day) => (
                      <button
                        key={day.value}
                        type="button"
                        onClick={() => toggleDay(day.value)}
                        className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                          formData.days_of_week.includes(day.value)
                            ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/10 text-[var(--gym-primary)]'
                            : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                        }`}
                        data-testid={`day-toggle-${day.value}`}
                      >
                        {day.label.slice(0, 3)}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Hora de inicio</label>
                    <Input
                      type="time"
                      value={formData.start_time}
                      onChange={(e) => updateField('start_time', e.target.value)}
                      className="input-dark"
                      data-testid="class-start-time"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Hora de fin</label>
                    <Input
                      type="time"
                      value={formData.end_time}
                      onChange={(e) => updateField('end_time', e.target.value)}
                      className="input-dark"
                      data-testid="class-end-time"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Fecha inicio (opcional)</label>
                    <Input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => updateField('start_date', e.target.value)}
                      className="input-dark"
                      data-testid="class-start-date"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Fecha fin (opcional)</label>
                    <Input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => updateField('end_date', e.target.value)}
                      className="input-dark"
                      data-testid="class-end-date"
                    />
                  </div>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Fecha</label>
                  <Input
                    type="date"
                    value={formData.single_date}
                    onChange={(e) => updateField('single_date', e.target.value)}
                    className="input-dark"
                    data-testid="class-single-date"
                  />
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Hora de inicio</label>
                  <Input
                    type="time"
                    value={formData.single_start_time}
                    onChange={(e) => updateField('single_start_time', e.target.value)}
                    className="input-dark"
                    data-testid="class-single-time"
                  />
                </div>
              </>
            )}

            <Button onClick={handleSaveClass} className="w-full btn-gym-primary" data-testid="save-class-btn">
              <Calendar size={20} className="mr-2" />
              {editClass ? 'Actualizar Clase' : 'Crear Clase'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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
            <div key={cls.id} className="stat-card relative group" data-testid={`class-card-${cls.id}`}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="absolute top-4 right-4 h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                    data-testid={`class-menu-${cls.id}`}
                  >
                    <MoreVertical size={16} />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-700">
                  <DropdownMenuItem onClick={() => openEdit(cls)} className="cursor-pointer" data-testid={`class-edit-${cls.id}`}>
                    <Edit size={16} className="mr-2" />
                    Editar
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-zinc-700" />
                  <DropdownMenuItem onClick={() => handleDeleteClass(cls.id)} className="cursor-pointer text-red-500" data-testid={`class-delete-${cls.id}`}>
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
                {cls.start_time && (
                  <div className="flex items-center gap-2 text-zinc-400">
                    <Clock size={16} />
                    <span>{cls.start_time}{cls.end_time ? ` - ${cls.end_time}` : ''} ({cls.duration_minutes} min)</span>
                  </div>
                )}
                {!cls.start_time && (
                  <div className="flex items-center gap-2 text-zinc-400">
                    <Clock size={16} />
                    <span>{cls.duration_minutes} minutos</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-zinc-400">
                  <Users size={16} />
                  <span>Max. {cls.max_capacity} personas</span>
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
                {cls.start_date && (
                  <div className="text-xs text-zinc-500 mt-1">
                    Desde {cls.start_date}{cls.end_date ? ` hasta ${cls.end_date}` : ''}
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
