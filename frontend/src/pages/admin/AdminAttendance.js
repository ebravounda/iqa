import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import { CheckCircle, XCircle, Users, Calendar, Clock, UserCheck, UserX } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminAttendance() {
  const { admin } = useAuth();
  const [schedules, setSchedules] = useState([]);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [attendance, setAttendance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTodaySchedules();
  }, []);

  const fetchTodaySchedules = async () => {
    try {
      const today = format(new Date(), 'yyyy-MM-dd');
      const response = await axios.get(`${API}/schedules`, {
        params: { date_from: today, date_to: today }
      });
      setSchedules(response.data);
      if (response.data.length > 0) {
        loadAttendance(response.data[0].id);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAttendance = async (scheduleId) => {
    try {
      setSelectedSchedule(scheduleId);
      const response = await axios.get(`${API}/attendance/schedule/${scheduleId}`);
      setAttendance(response.data);
    } catch (error) {
      toast.error('Error al cargar asistencia');
    }
  };

  const handleCheckin = async (bookingId) => {
    try {
      await axios.post(`${API}/bookings/${bookingId}/checkin`);
      toast.success('Check-in registrado');
      loadAttendance(selectedSchedule);
    } catch (error) {
      toast.error('Error al registrar check-in');
    }
  };

  const handleCheckout = async (bookingId) => {
    try {
      await axios.post(`${API}/bookings/${bookingId}/checkout`);
      toast.success('Check-in anulado');
      loadAttendance(selectedSchedule);
    } catch (error) {
      toast.error('Error al anular check-in');
    }
  };

  const formatTime = (t) => t || '--:--';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-attendance">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Asistencia a Clases</h1>
        <p className="text-zinc-400 text-sm">Registra la asistencia de los socios a sus clases</p>
      </div>

      {/* Schedule Selector */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <Calendar size={18} className="text-zinc-400" />
          <h3 className="font-bold">Clases de Hoy - {format(new Date(), "d 'de' MMMM, yyyy", { locale: es })}</h3>
        </div>

        {schedules.length === 0 ? (
          <p className="text-zinc-500 text-sm">No hay clases programadas para hoy</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {schedules.map((s) => (
              <button
                key={s.id}
                onClick={() => loadAttendance(s.id)}
                className={`text-left p-4 rounded-xl border transition-all ${
                  selectedSchedule === s.id
                    ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/5'
                    : 'border-zinc-800 hover:border-zinc-600'
                }`}
                data-testid={`schedule-card-${s.id}`}
              >
                <p className="font-bold text-sm">{s.class?.name || 'Clase'}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400">
                  <Clock size={12} />
                  <span>{formatTime(s.start_time)} - {formatTime(s.end_time)}</span>
                </div>
                {s.trainer && (
                  <p className="text-xs text-zinc-500 mt-1">Trainer: {s.trainer.name}</p>
                )}
                <div className="flex items-center gap-1 mt-2 text-xs">
                  <Users size={12} />
                  <span>{s.current_bookings}/{s.max_capacity} reservas</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Attendance List */}
      {attendance && (
        <div className="stat-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-bold text-lg">{attendance.class?.name || 'Clase'}</h3>
              <p className="text-zinc-400 text-sm">
                {attendance.schedule?.start_time} - {attendance.schedule?.end_time}
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <UserCheck size={16} className="text-emerald-400" />
                <span className="font-bold text-emerald-400">{attendance.checked_in}</span>
                <span className="text-zinc-500">presentes</span>
              </div>
              <div className="flex items-center gap-2">
                <UserX size={16} className="text-zinc-500" />
                <span className="font-bold">{attendance.pending}</span>
                <span className="text-zinc-500">pendientes</span>
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="w-full h-2 bg-zinc-800 rounded-full mb-6 overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-500"
              style={{
                width: `${attendance.total_booked > 0 ? (attendance.checked_in / attendance.total_booked * 100) : 0}%`
              }}
            />
          </div>

          {attendance.bookings.length === 0 ? (
            <p className="text-zinc-500 text-center py-8">No hay reservas para esta clase</p>
          ) : (
            <div className="space-y-2">
              {attendance.bookings.map((booking) => (
                <div
                  key={booking.id}
                  className={`flex items-center justify-between p-4 rounded-xl border transition-all ${
                    booking.checked_in
                      ? 'border-emerald-500/30 bg-emerald-500/5'
                      : 'border-zinc-800'
                  }`}
                  data-testid={`booking-row-${booking.id}`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                      booking.checked_in 
                        ? 'bg-emerald-500/20 text-emerald-400' 
                        : 'bg-zinc-800 text-zinc-400'
                    }`}>
                      {booking.member_name?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <p className="font-medium">{booking.member_name}</p>
                      <p className="text-xs text-zinc-500">
                        <code className="bg-zinc-800 px-1.5 py-0.5 rounded">{booking.member_code}</code>
                        {booking.checked_in && booking.checked_in_at && (
                          <span className="ml-2 text-emerald-400">
                            Check-in: {format(new Date(booking.checked_in_at), 'HH:mm')}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  {booking.checked_in ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCheckout(booking.id)}
                      className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      data-testid={`undo-checkin-${booking.id}`}
                    >
                      <XCircle size={18} className="mr-1" />
                      Anular
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => handleCheckin(booking.id)}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white"
                      data-testid={`checkin-btn-${booking.id}`}
                    >
                      <CheckCircle size={18} className="mr-1" />
                      Check-in
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
