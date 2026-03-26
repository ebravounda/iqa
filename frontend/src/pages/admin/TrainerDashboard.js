import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';
import { 
  Calendar, Clock, Users, CheckCircle, XCircle, 
  UserCheck, TrendingUp, Dumbbell, ChevronRight
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function TrainerDashboard() {
  const { admin } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await axios.get(`${API}/trainer/dashboard`);
      setData(res.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckin = async (bookingId) => {
    try {
      await axios.post(`${API}/bookings/${bookingId}/checkin`);
      toast.success('Check-in registrado');
      fetchDashboard();
    } catch (error) {
      toast.error('Error al registrar check-in');
    }
  };

  const handleCheckout = async (bookingId) => {
    try {
      await axios.post(`${API}/bookings/${bookingId}/checkout`);
      toast.success('Check-in anulado');
      fetchDashboard();
    } catch (error) {
      toast.error('Error al anular');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const ws = data?.week_stats || {};

  return (
    <div className="space-y-6" data-testid="trainer-dashboard">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Mi Panel - Trainer</h1>
        <p className="text-zinc-400 text-sm">Hola, {admin?.name} - {format(new Date(), "EEEE d 'de' MMMM", { locale: es })}</p>
      </div>

      {/* Week Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card" data-testid="trainer-stat-classes">
          <div className="flex items-center justify-between mb-3">
            <span className="text-zinc-400 text-xs font-medium">Mis Clases</span>
            <Dumbbell size={18} className="text-[var(--gym-primary)]" />
          </div>
          <p className="text-2xl font-black">{data?.total_classes || 0}</p>
        </div>
        <div className="stat-card" data-testid="trainer-stat-week-schedules">
          <div className="flex items-center justify-between mb-3">
            <span className="text-zinc-400 text-xs font-medium">Esta Semana</span>
            <Calendar size={18} className="text-blue-400" />
          </div>
          <p className="text-2xl font-black">{ws.total_schedules || 0}</p>
          <p className="text-xs text-zinc-500">sesiones</p>
        </div>
        <div className="stat-card" data-testid="trainer-stat-week-bookings">
          <div className="flex items-center justify-between mb-3">
            <span className="text-zinc-400 text-xs font-medium">Reservas Semana</span>
            <Users size={18} className="text-purple-400" />
          </div>
          <p className="text-2xl font-black">{ws.total_bookings || 0}</p>
        </div>
        <div className="stat-card" data-testid="trainer-stat-attendance">
          <div className="flex items-center justify-between mb-3">
            <span className="text-zinc-400 text-xs font-medium">Asistencia</span>
            <TrendingUp size={18} className="text-emerald-400" />
          </div>
          <p className="text-2xl font-black">{ws.attendance_rate || 0}%</p>
          <p className="text-xs text-zinc-500">{ws.total_checkins || 0} check-ins</p>
        </div>
      </div>

      {/* Today's Classes */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <Calendar size={18} style={{ color: 'var(--gym-primary)' }} />
          <h3 className="font-bold text-lg">Clases de Hoy</h3>
          <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full ml-auto">
            {data?.today_schedules?.length || 0} clases
          </span>
        </div>

        {(!data?.today_schedules || data.today_schedules.length === 0) ? (
          <p className="text-zinc-500 text-sm py-6 text-center">No tienes clases programadas para hoy</p>
        ) : (
          <div className="space-y-4">
            {data.today_schedules.map((s) => (
              <div key={s.id} className="border border-zinc-800 rounded-xl p-4" data-testid={`trainer-schedule-${s.id}`}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="font-bold">{s.class?.name || 'Clase'}</p>
                    <div className="flex items-center gap-2 text-xs text-zinc-400 mt-1">
                      <Clock size={12} />
                      <span>{s.start_time} - {s.end_time}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-sm">
                      <UserCheck size={14} className="text-emerald-400" />
                      <span className="font-bold text-emerald-400">{s.checked_in_count}</span>
                      <span className="text-zinc-500">/ {s.bookings?.length || 0}</span>
                    </div>
                    <p className="text-[10px] text-zinc-500">asistentes</p>
                  </div>
                </div>

                {/* Progress */}
                {s.bookings && s.bookings.length > 0 && (
                  <div className="w-full h-1.5 bg-zinc-800 rounded-full mb-3 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{ width: `${(s.checked_in_count / s.bookings.length) * 100}%` }}
                    />
                  </div>
                )}

                {/* Attendee list */}
                {s.bookings && s.bookings.length > 0 ? (
                  <div className="space-y-1.5">
                    {s.bookings.map((b) => (
                      <div key={b.id} className={`flex items-center justify-between py-2 px-3 rounded-lg ${
                        b.checked_in ? 'bg-emerald-500/5 border border-emerald-500/20' : 'bg-zinc-800/50'
                      }`}>
                        <div className="flex items-center gap-2">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                            b.checked_in ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'
                          }`}>
                            {b.member_name?.charAt(0)?.toUpperCase() || '?'}
                          </div>
                          <div>
                            <p className="text-sm font-medium">{b.member_name}</p>
                            <code className="text-[10px] text-zinc-500">{b.member_code}</code>
                          </div>
                        </div>
                        {b.checked_in ? (
                          <Button variant="ghost" size="sm" className="h-7 text-xs text-red-400 hover:text-red-300"
                            onClick={() => handleCheckout(b.id)} data-testid={`trainer-undo-${b.id}`}>
                            <XCircle size={14} className="mr-1" /> Anular
                          </Button>
                        ) : (
                          <Button size="sm" className="h-7 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
                            onClick={() => handleCheckin(b.id)} data-testid={`trainer-checkin-${b.id}`}>
                            <CheckCircle size={14} className="mr-1" /> Check-in
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-xs text-center py-2">Sin reservas</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming */}
      {data?.upcoming_schedules && data.upcoming_schedules.length > 0 && (
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-4">
            <ChevronRight size={18} className="text-blue-400" />
            <h3 className="font-bold text-lg">Proximas Clases</h3>
          </div>
          <div className="space-y-2">
            {data.upcoming_schedules.map((u) => (
              <div key={u.id} className="flex items-center justify-between py-3 px-4 border border-zinc-800 rounded-lg">
                <div>
                  <p className="font-medium text-sm">{u.class?.name || 'Clase'}</p>
                  <p className="text-xs text-zinc-500">{u.start_time} - {u.end_time}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{format(new Date(u.date + 'T12:00:00'), "EEE d MMM", { locale: es })}</p>
                  <p className="text-xs text-zinc-500">{u.current_bookings}/{u.max_capacity} reservas</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
