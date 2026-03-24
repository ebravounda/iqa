import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';
import { Bell, Check, Calendar, Users, Tag, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NOTIFICATION_ICONS = {
  general: Bell,
  class: Calendar,
  membership: Users,
  promotion: Tag
};

export default function MemberNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications/member`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.post(`${API}/notifications/${notificationId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6" data-testid="member-notifications">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Notificaciones</h1>
          <p className="text-zinc-400 text-sm">
            {unreadCount > 0 ? `${unreadCount} sin leer` : 'Todo al día'}
          </p>
        </div>
        {unreadCount > 0 && (
          <div 
            className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
          >
            {unreadCount}
          </div>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-5 w-40 mb-2" />
              <div className="skeleton h-4 w-full" />
            </div>
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-16">
          <Bell size={48} className="mx-auto text-zinc-700 mb-4" />
          <p className="text-zinc-500">No hay notificaciones</p>
          <p className="text-zinc-600 text-sm">Te avisaremos cuando haya novedades</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((notification, index) => {
            const Icon = NOTIFICATION_ICONS[notification.notification_type] || Bell;
            return (
              <motion.div
                key={notification.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => !notification.is_read && markAsRead(notification.id)}
                className={`stat-card cursor-pointer transition-colors ${
                  !notification.is_read ? 'border-[var(--gym-primary)]/30 bg-[var(--gym-primary)]/5' : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    !notification.is_read ? 'bg-[var(--gym-primary)]/20' : 'bg-zinc-800'
                  }`}>
                    <Icon 
                      size={20} 
                      className={!notification.is_read ? '' : 'text-zinc-500'}
                      style={!notification.is_read ? { color: 'var(--gym-primary)' } : {}}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className={`font-bold ${!notification.is_read ? '' : 'text-zinc-300'}`}>
                        {notification.title}
                      </h3>
                      {!notification.is_read && (
                        <div 
                          className="w-2 h-2 rounded-full shrink-0 mt-2"
                          style={{ backgroundColor: 'var(--gym-primary)' }}
                        />
                      )}
                    </div>
                    <p className={`text-sm mt-1 ${!notification.is_read ? 'text-zinc-300' : 'text-zinc-500'}`}>
                      {notification.message}
                    </p>
                    <p className="text-xs text-zinc-600 mt-2">
                      {format(new Date(notification.created_at), "d MMM, HH:mm", { locale: es })}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
