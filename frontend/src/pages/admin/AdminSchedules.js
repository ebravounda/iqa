import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Calendar } from '../../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../../components/ui/popover';
import { 
  Plus, Calendar as CalendarIcon, Clock, Users, User, X, Eye
} from 'lucide-react';
import { toast } from 'sonner';
import { format, addDays, startOfWeek } from 'date-fns';
import { es } from 'date-fns/locale';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminSchedules() {
  const { admin } = useAuth();
  const [schedules, setSchedules] = useState([]);
  const [classes, setClasses] = useState([]);
  const [trainers, setTrainers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAttendeesModal, setShowAttendeesModal] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [attendees, setAttendees] = useState([]);
  const [newSchedule, setNewSchedule] = useState({
    class_id: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    start_time: '09:00',
    end_time: '10:00',
    trainer_id: '',
    max_capacity: ''
  });

  useEffect(() => {
    fetchSchedules();
    fetchClasses();
    fetchTrainers();
  }, [selectedDate]);

  const fetchSchedules = async () => {
    try {
      const dateFrom = format(startOfWeek(selectedDate, { weekStartsOn: 1 }), 'yyyy-MM-dd');
      const dateTo = format(addDays(startOfWeek(selectedDate, { weekStartsOn: 1 }), 6), 'yyyy-MM-dd');
      const response = await axios.get(`${API}/schedules?date_from=${dateFrom}&date_to=${dateTo}`);
      setSchedules(response.data);
    } catch (error) {
      toast.error('Error al cargar horarios');
    } finally {
      setLoading(false);
    }
  };

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API}/classes`);
      setClasses(response.data);
    } catch (error) {
      console.error('Error fetching classes:', error);
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

  const handleCreateSchedule = async () => {
    if (!newSchedule.class_id || !newSchedule.date || !newSchedule.start_time) {
      toast.error('Completa los campos requeridos');
      return;
    }

    try {
      await axios.post(`${API}/schedules`, {
        ...newSchedule,
        trainer_id: newSchedule.trainer_id || null,
        max_capacity: newSchedule.max_capacity ? parseInt(newSchedule.max_capacity) : null
      });
      toast.success('Horario creado');
      setShowCreateModal(false);
      setNewSchedule({
        class_id: '',
        date: format(new Date(), 'yyyy-MM-dd'),
        start_time: '09:00',
        end_time: '10:00',
        trainer_id: '',
        max_capacity: ''
      });
      fetchSchedules();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear horario');
    }
  };

  const handleCancelSchedule = async (scheduleId) => {
    if (!window.confirm('¿Cancelar esta clase?')) return;
    
    try {
      await axios.put(`${API}/schedules/${scheduleId}/cancel`);
      toast.success('Clase cancelada');
      fetchSchedules();
    } catch (error) {
      toast.error('Error al cancelar');
    }
  };

  const handleViewAttendees = async (schedule) => {
    try {
      const response = await axios.get(`${API}/bookings/schedule/${schedule.id}/attendees`);
      setAttendees(response.data);
      setSelectedSchedule(schedule);
      setShowAttendeesModal(true);
    } catch (error) {
      toast.error('Error al cargar asistentes');
    }
  };

  // Group schedules by date
  const schedulesByDate = schedules.reduce((acc, schedule) => {
    if (!acc[schedule.date]) {
      acc[schedule.date] = [];
    }
    acc[schedule.date].push(schedule);
    return acc;
  }, {});

  // Generate week days
  const weekStart = startOfWeek(selectedDate, { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  return (
    <div className="space-y-6" data-testid="admin-schedules">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Horarios de Clases</h1>
          <p className="text-zinc-400 text-sm">
            Semana del {format(weekStart, "d 'de' MMMM", { locale: es })}
          </p>
        </div>
        
        <div className="flex gap-3">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="border-zinc-700">
                <CalendarIcon size={18} className="mr-2" />
                {format(selectedDate, 'dd/MM/yyyy')}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0 bg-zinc-900 border-zinc-700">
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={(date) => date && setSelectedDate(date)}
                locale={es}
              />
            </PopoverContent>
          </Popover>

          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button className="btn-gym-primary" data-testid="create-schedule-btn">
                <Plus size={20} className="mr-2" />
                Agregar Horario
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-zinc-800">
              <DialogHeader>
                <DialogTitle>Agregar Horario</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Clase</label>
                  <Select value={newSchedule.class_id} onValueChange={(v) => setNewSchedule({ ...newSchedule, class_id: v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue placeholder="Seleccionar clase" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      {classes.map((c) => (
                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Fecha</label>
                  <Input
                    type="date"
                    value={newSchedule.date}
                    onChange={(e) => setNewSchedule({ ...newSchedule, date: e.target.value })}
                    className="input-dark"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Hora Inicio</label>
                    <Input
                      type="time"
                      value={newSchedule.start_time}
                      onChange={(e) => setNewSchedule({ ...newSchedule, start_time: e.target.value })}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 mb-1 block">Hora Fin</label>
                    <Input
                      type="time"
                      value={newSchedule.end_time}
                      onChange={(e) => setNewSchedule({ ...newSchedule, end_time: e.target.value })}
                      className="input-dark"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Entrenador (opcional)</label>
                  <Select value={newSchedule.trainer_id} onValueChange={(v) => setNewSchedule({ ...newSchedule, trainer_id: v === "default" ? "" : v })}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="default">Usar default de clase</SelectItem>
                      {trainers.map((t) => (
                        <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button onClick={handleCreateSchedule} className="w-full btn-gym-primary">
                  <CalendarIcon size={20} className="mr-2" />
                  Crear Horario
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Week View */}
      <div className="grid grid-cols-7 gap-4">
        {weekDays.map((day) => {
          const dateStr = format(day, 'yyyy-MM-dd');
          const daySchedules = schedulesByDate[dateStr] || [];
          const isToday = format(new Date(), 'yyyy-MM-dd') === dateStr;
          
          return (
            <div key={dateStr} className="min-h-[300px]">
              <div className={`text-center py-2 rounded-t-lg ${
                isToday ? 'bg-[var(--gym-primary)] text-black' : 'bg-zinc-800'
              }`}>
                <p className="text-xs font-medium">{format(day, 'EEE', { locale: es })}</p>
                <p className="text-lg font-bold">{format(day, 'd')}</p>
              </div>
              
              <div className="bg-zinc-900/50 border border-zinc-800 border-t-0 rounded-b-lg p-2 space-y-2 min-h-[250px]">
                {daySchedules.length === 0 ? (
                  <p className="text-zinc-600 text-xs text-center py-4">Sin clases</p>
                ) : (
                  daySchedules.sort((a, b) => a.start_time.localeCompare(b.start_time)).map((schedule) => (
                    <div 
                      key={schedule.id}
                      className={`p-2 rounded-lg text-xs ${
                        schedule.status === 'cancelled' 
                          ? 'bg-red-500/10 border border-red-500/20' 
                          : 'bg-zinc-800 hover:bg-zinc-700'
                      } cursor-pointer transition-colors`}
                      onClick={() => handleViewAttendees(schedule)}
                    >
                      <p className="font-bold truncate">{schedule.class?.name}</p>
                      <p className="text-zinc-400">{schedule.start_time} - {schedule.end_time}</p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-zinc-500">
                          {schedule.current_bookings}/{schedule.max_capacity}
                        </span>
                        {schedule.status !== 'cancelled' && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleCancelSchedule(schedule.id); }}
                            className="text-red-500 hover:text-red-400"
                          >
                            <X size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Attendees Modal */}
      <Dialog open={showAttendeesModal} onOpenChange={setShowAttendeesModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle>
              Asistentes - {selectedSchedule?.class?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            <div className="flex items-center gap-4 mb-4 p-3 bg-zinc-800 rounded-lg">
              <div className="flex items-center gap-2 text-zinc-400">
                <CalendarIcon size={16} />
                <span>{selectedSchedule?.date}</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-400">
                <Clock size={16} />
                <span>{selectedSchedule?.start_time} - {selectedSchedule?.end_time}</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-400">
                <Users size={16} />
                <span>{attendees.length}/{selectedSchedule?.max_capacity}</span>
              </div>
            </div>

            {attendees.length === 0 ? (
              <p className="text-center text-zinc-500 py-8">No hay reservas para esta clase</p>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {attendees.map((booking) => (
                  <div key={booking.id} className="flex items-center justify-between p-3 bg-zinc-800 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center font-bold text-sm">
                        {booking.member_name?.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium">{booking.member_name}</p>
                        <p className="text-xs text-zinc-500">{booking.member_code}</p>
                      </div>
                    </div>
                    <span className={`badge ${
                      booking.status === 'confirmed' ? 'badge-success' : 'badge-danger'
                    }`}>
                      {booking.status === 'confirmed' ? 'Confirmado' : 'Cancelado'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
