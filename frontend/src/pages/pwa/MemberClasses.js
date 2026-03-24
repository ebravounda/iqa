import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { formatDate } from '../../lib/utils';
import { Button } from '../../components/ui/button';
import { motion } from 'framer-motion';
import { Calendar, Clock, Users, User, Check, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { format, addDays, startOfWeek } from 'date-fns';
import { es } from 'date-fns/locale';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MemberClasses() {
  const { gym, member } = useAuth();
  const [schedules, setSchedules] = useState([]);
  const [myBookings, setMyBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [bookingInProgress, setBookingInProgress] = useState(null);

  useEffect(() => {
    if (gym?.id) {
      fetchSchedules();
      fetchMyBookings();
    }
  }, [gym, selectedDate]);

  const fetchSchedules = async () => {
    try {
      const dateFrom = format(selectedDate, 'yyyy-MM-dd');
      const dateTo = format(addDays(selectedDate, 7), 'yyyy-MM-dd');
      const response = await axios.get(`${API}/schedules/public/${gym.id}?date_from=${dateFrom}&date_to=${dateTo}`);
      setSchedules(response.data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyBookings = async () => {
    try {
      const response = await axios.get(`${API}/bookings/member`);
      setMyBookings(response.data);
    } catch (error) {
      console.error('Error fetching bookings:', error);
    }
  };

  const handleBook = async (scheduleId) => {
    setBookingInProgress(scheduleId);
    try {
      await axios.post(`${API}/bookings`, { schedule_id: scheduleId });
      toast.success('¡Reserva confirmada!');
      fetchSchedules();
      fetchMyBookings();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al reservar');
    } finally {
      setBookingInProgress(null);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    try {
      await axios.delete(`${API}/bookings/${bookingId}`);
      toast.success('Reserva cancelada');
      fetchSchedules();
      fetchMyBookings();
    } catch (error) {
      toast.error('Error al cancelar');
    }
  };

  const isBooked = (scheduleId) => {
    return myBookings.some(b => b.schedule_id === scheduleId && b.status === 'confirmed');
  };

  const getBookingId = (scheduleId) => {
    const booking = myBookings.find(b => b.schedule_id === scheduleId && b.status === 'confirmed');
    return booking?.id;
  };

  // Generate days for the week
  const weekStart = startOfWeek(selectedDate, { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  // Group schedules by date
  const schedulesByDate = schedules.reduce((acc, schedule) => {
    if (!acc[schedule.date]) {
      acc[schedule.date] = [];
    }
    acc[schedule.date].push(schedule);
    return acc;
  }, {});

  const goToPreviousWeek = () => {
    setSelectedDate(prev => addDays(prev, -7));
  };

  const goToNextWeek = () => {
    setSelectedDate(prev => addDays(prev, 7));
  };

  return (
    <div className="space-y-5 sm:space-y-6" data-testid="member-classes">
      <div>
        <h1 className="text-xl sm:text-2xl font-black tracking-tight">Clases</h1>
        <p className="text-zinc-400 text-xs sm:text-sm">Reserva tu lugar en las clases</p>
      </div>

      {/* Week Navigation */}
      <div className="flex items-center justify-between">
        <button 
          onClick={goToPreviousWeek}
          className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors"
        >
          <ChevronLeft size={20} />
        </button>
        <div className="text-center">
          <p className="font-bold">
            {format(weekStart, "d MMM", { locale: es })} - {format(addDays(weekStart, 6), "d MMM yyyy", { locale: es })}
          </p>
        </div>
        <button 
          onClick={goToNextWeek}
          className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Day Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {weekDays.map((day) => {
          const dateStr = format(day, 'yyyy-MM-dd');
          const isToday = format(new Date(), 'yyyy-MM-dd') === dateStr;
          const hasClasses = schedulesByDate[dateStr]?.length > 0;
          
          return (
            <button
              key={dateStr}
              onClick={() => setSelectedDate(day)}
              className={`flex-shrink-0 px-4 py-3 rounded-xl text-center transition-colors ${
                format(selectedDate, 'yyyy-MM-dd') === dateStr
                  ? 'bg-[var(--gym-primary)] text-black'
                  : isToday
                  ? 'bg-zinc-700 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              <p className="text-xs font-medium">{format(day, 'EEE', { locale: es })}</p>
              <p className="text-lg font-bold">{format(day, 'd')}</p>
              {hasClasses && format(selectedDate, 'yyyy-MM-dd') !== dateStr && (
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--gym-primary)] mx-auto mt-1" />
              )}
            </button>
          );
        })}
      </div>

      {/* Classes List */}
      <div className="space-y-4">
        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-6 w-32 mb-2" />
              <div className="skeleton h-4 w-24" />
            </div>
          ))
        ) : (schedulesByDate[format(selectedDate, 'yyyy-MM-dd')] || []).length === 0 ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <Calendar size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay clases programadas</p>
            <p className="text-zinc-600 text-sm">para este día</p>
          </motion.div>
        ) : (
          (schedulesByDate[format(selectedDate, 'yyyy-MM-dd')] || [])
            .sort((a, b) => a.start_time.localeCompare(b.start_time))
            .map((schedule, index) => {
              const booked = isBooked(schedule.id);
              const isFull = schedule.spots_available <= 0;
              
              return (
                <motion.div
                  key={schedule.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`stat-card ${booked ? 'border-[var(--gym-primary)]/50' : ''}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-lg">{schedule.class?.name}</h3>
                      {schedule.class?.description && (
                        <p className="text-zinc-500 text-sm">{schedule.class.description}</p>
                      )}
                    </div>
                    {booked && (
                      <span className="badge badge-success flex items-center gap-1">
                        <Check size={12} />
                        Reservado
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-4 mb-4 text-sm">
                    <div className="flex items-center gap-2 text-zinc-400">
                      <Clock size={16} />
                      <span>{schedule.start_time} - {schedule.end_time}</span>
                    </div>
                    <div className="flex items-center gap-2 text-zinc-400">
                      <Users size={16} />
                      <span className={isFull && !booked ? 'text-red-400' : ''}>
                        {schedule.spots_available} lugares disponibles
                      </span>
                    </div>
                    {schedule.trainer && (
                      <div className="flex items-center gap-2 text-zinc-400">
                        <User size={16} />
                        <span>{schedule.trainer.name}</span>
                      </div>
                    )}
                  </div>

                  {booked ? (
                    <Button
                      onClick={() => handleCancelBooking(getBookingId(schedule.id))}
                      variant="outline"
                      className="w-full border-red-500/50 text-red-400 hover:bg-red-500/10"
                    >
                      <X size={18} className="mr-2" />
                      Cancelar Reserva
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handleBook(schedule.id)}
                      disabled={isFull || bookingInProgress === schedule.id}
                      className={`w-full ${isFull ? 'opacity-50' : 'btn-gym-primary'}`}
                    >
                      {bookingInProgress === schedule.id ? (
                        <span className="animate-pulse">Reservando...</span>
                      ) : isFull ? (
                        'Clase Llena'
                      ) : (
                        <>
                          <Check size={18} className="mr-2" />
                          Reservar
                        </>
                      )}
                    </Button>
                  )}
                </motion.div>
              );
            })
        )}
      </div>

      {/* My Upcoming Bookings */}
      {myBookings.filter(b => b.status === 'confirmed' && new Date(b.date) >= new Date()).length > 0 && (
        <div className="pt-6 border-t border-zinc-800">
          <h2 className="font-bold text-lg mb-4">Mis Próximas Reservas</h2>
          <div className="space-y-3">
            {myBookings
              .filter(b => b.status === 'confirmed' && new Date(b.date) >= new Date())
              .sort((a, b) => new Date(a.date) - new Date(b.date))
              .slice(0, 3)
              .map((booking) => (
                <div key={booking.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-xl">
                  <div>
                    <p className="font-medium">{booking.class?.name}</p>
                    <p className="text-sm text-zinc-400">
                      {format(new Date(booking.date), "EEEE d MMM", { locale: es })} • {booking.schedule?.start_time}
                    </p>
                  </div>
                  <button
                    onClick={() => handleCancelBooking(booking.id)}
                    className="text-zinc-500 hover:text-red-400 p-2"
                  >
                    <X size={18} />
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
