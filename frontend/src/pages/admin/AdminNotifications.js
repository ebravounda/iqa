import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Bell, Plus, Trash2, Send, Users, Calendar, Tag, MoreVertical
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NOTIFICATION_TYPES = [
  { value: 'general', label: 'General', icon: Bell },
  { value: 'class', label: 'Clases', icon: Calendar },
  { value: 'membership', label: 'Membresías', icon: Users },
  { value: 'promotion', label: 'Promoción', icon: Tag },
];

export default function AdminNotifications() {
  const { admin } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [gyms, setGyms] = useState([]);
  const [newNotification, setNewNotification] = useState({
    title: '',
    message: '',
    notification_type: 'general',
    target: 'all',
    gym_id: admin?.gym_id || ''
  });

  useEffect(() => {
    fetchNotifications();
    if (admin?.role === 'super_admin') {
      fetchGyms();
    }
  }, []);

  const fetchGyms = async () => {
    try {
      const response = await axios.get(`${API}/gyms`);
      setGyms(response.data);
    } catch (error) {
      console.error('Error fetching gyms:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newNotification.title || !newNotification.message) {
      toast.error('Título y mensaje son requeridos');
      return;
    }

    const gymId = admin?.gym_id || newNotification.gym_id;
    if (!gymId) {
      toast.error('Selecciona un gimnasio');
      return;
    }

    try {
      await axios.post(`${API}/notifications`, {
        ...newNotification,
        gym_id: gymId
      });
      toast.success('Notificación enviada a todos los socios');
      setShowCreateModal(false);
      setNewNotification({
        title: '',
        message: '',
        notification_type: 'general',
        target: 'all',
        gym_id: admin?.gym_id || ''
      });
      fetchNotifications();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear notificación');
    }
  };

  const handleDelete = async (notificationId) => {
    if (!window.confirm('¿Eliminar esta notificación?')) return;
    
    try {
      await axios.delete(`${API}/notifications/${notificationId}`);
      toast.success('Notificación eliminada');
      fetchNotifications();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const getTypeIcon = (type) => {
    const found = NOTIFICATION_TYPES.find(t => t.value === type);
    return found ? found.icon : Bell;
  };

  const getTypeLabel = (type) => {
    const found = NOTIFICATION_TYPES.find(t => t.value === type);
    return found ? found.label : type;
  };

  return (
    <div className="space-y-6" data-testid="admin-notifications">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Notificaciones</h1>
          <p className="text-zinc-400 text-sm">Envía mensajes a todos los socios</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="create-notification-btn">
              <Plus size={20} className="mr-2" />
              Nueva Notificación
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
            <DialogHeader>
              <DialogTitle>Enviar Notificación</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {admin?.role === 'super_admin' && (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Gimnasio</label>
                  <Select 
                    value={newNotification.gym_id} 
                    onValueChange={(v) => setNewNotification({ ...newNotification, gym_id: v })}
                  >
                    <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="notification-gym-select">
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
                <label className="text-sm text-zinc-400 mb-1 block">Título</label>
                <Input
                  value={newNotification.title}
                  onChange={(e) => setNewNotification({ ...newNotification, title: e.target.value })}
                  placeholder="Ej: Nueva clase disponible"
                  className="input-dark"
                  data-testid="notification-title-input"
                />
              </div>

              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Mensaje</label>
                <Textarea
                  value={newNotification.message}
                  onChange={(e) => setNewNotification({ ...newNotification, message: e.target.value })}
                  placeholder="Escribe el mensaje para los socios..."
                  className="input-dark min-h-[120px]"
                  data-testid="notification-message-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Tipo</label>
                  <Select 
                    value={newNotification.notification_type} 
                    onValueChange={(v) => setNewNotification({ ...newNotification, notification_type: v })}
                  >
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      {NOTIFICATION_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Destinatarios</label>
                  <Select 
                    value={newNotification.target} 
                    onValueChange={(v) => setNewNotification({ ...newNotification, target: v })}
                  >
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="all">Todos los socios</SelectItem>
                      <SelectItem value="active_members">Solo activos</SelectItem>
                      <SelectItem value="expiring_members">Por vencer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button onClick={handleCreate} className="w-full btn-gym-primary" data-testid="send-notification-btn">
                <Send size={20} className="mr-2" />
                Enviar Notificación
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-6 w-48 mb-2" />
              <div className="skeleton h-4 w-full" />
            </div>
          ))
        ) : notifications.length === 0 ? (
          <div className="text-center py-12">
            <Bell size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay notificaciones enviadas</p>
            <p className="text-zinc-600 text-sm">Crea una para comunicarte con tus socios</p>
          </div>
        ) : (
          notifications.map((notification) => {
            const TypeIcon = getTypeIcon(notification.notification_type);
            return (
              <div key={notification.id} className="stat-card">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center shrink-0">
                      <TypeIcon size={20} style={{ color: 'var(--gym-primary)' }} />
                    </div>
                    <div>
                      <h3 className="font-bold">{notification.title}</h3>
                      <p className="text-zinc-400 text-sm mt-1 whitespace-pre-wrap">{notification.message}</p>
                      <div className="flex items-center gap-4 mt-3 text-xs text-zinc-500">
                        <span className="badge badge-primary">{getTypeLabel(notification.notification_type)}</span>
                        <span>{format(new Date(notification.created_at), "d MMM yyyy, HH:mm", { locale: es })}</span>
                        <span>{notification.read_by?.length || 0} lecturas</span>
                      </div>
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
                        onClick={() => handleDelete(notification.id)} 
                        className="cursor-pointer text-red-500"
                      >
                        <Trash2 size={16} className="mr-2" />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
