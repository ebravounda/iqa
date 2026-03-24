import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { formatDate, formatDateTime } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { motion, AnimatePresence } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';
import { 
  UserPlus, Users, Clock, Check, X, QrCode, ChevronRight, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MemberGuests() {
  const { member } = useAuth();
  const [guests, setGuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const [selectedGuest, setSelectedGuest] = useState(null);
  const [guestQR, setGuestQR] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [newGuest, setNewGuest] = useState({
    name: '',
    phone: '',
    valid_days: '1'
  });

  const canBringGuests = member?.can_bring_guests;

  useEffect(() => {
    fetchGuests();
  }, []);

  const fetchGuests = async () => {
    try {
      const response = await axios.get(`${API}/guests/member`);
      setGuests(response.data);
    } catch (error) {
      console.error('Error fetching guests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGuest = async () => {
    if (!newGuest.name) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      await axios.post(`${API}/guests`, {
        name: newGuest.name,
        phone: newGuest.phone || null,
        valid_days: parseInt(newGuest.valid_days)
      });
      toast.success('Pase de invitado creado');
      setShowCreateModal(false);
      setNewGuest({ name: '', phone: '', valid_days: '1' });
      fetchGuests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear pase');
    }
  };

  const fetchGuestQR = useCallback(async (guestCode) => {
    try {
      const response = await axios.get(`${API}/guests/${guestCode}/qr`);
      setGuestQR(response.data);
      setCountdown(response.data.refresh_seconds);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al generar QR');
      setShowQRModal(false);
    }
  }, []);

  const showGuestQR = (guest) => {
    setSelectedGuest(guest);
    setShowQRModal(true);
    fetchGuestQR(guest.code);
  };

  // Countdown timer for guest QR
  useEffect(() => {
    if (!showQRModal || !selectedGuest) return;
    
    if (countdown <= 0) {
      fetchGuestQR(selectedGuest.code);
      return;
    }

    const timer = setInterval(() => {
      setCountdown(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown, showQRModal, selectedGuest, fetchGuestQR]);

  const getStatusBadge = (guest) => {
    const now = new Date();
    const validUntil = new Date(guest.valid_until);
    
    if (guest.status === 'expired' || validUntil < now) {
      return <span className="badge badge-danger">Expirado</span>;
    }
    return <span className="badge badge-success">Activo</span>;
  };

  const activeGuests = guests.filter(g => {
    const validUntil = new Date(g.valid_until);
    return g.status === 'active' && validUntil >= new Date();
  });

  if (!canBringGuests) {
    return (
      <div className="space-y-6" data-testid="member-guests">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Invitados</h1>
          <p className="text-zinc-400 text-sm">Trae amigos al gimnasio</p>
        </div>

        <div className="text-center py-12">
          <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={32} className="text-zinc-500" />
          </div>
          <h3 className="font-bold text-lg mb-2">Sin permiso de invitados</h3>
          <p className="text-zinc-500 max-w-sm mx-auto">
            Tu membresía actual no incluye la opción de traer invitados. 
            Consulta en recepción para activar esta función.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="member-guests">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Mis Invitados</h1>
          <p className="text-zinc-400 text-sm">
            {member?.max_guests_per_month || 2} invitados permitidos/mes
          </p>
        </div>
      </div>

      {/* Create Guest Button */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogTrigger asChild>
          <Button className="w-full btn-gym-primary h-14" data-testid="create-guest-btn">
            <UserPlus size={24} className="mr-3" />
            Crear Pase de Invitado
          </Button>
        </DialogTrigger>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle>Nuevo Pase de Invitado</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Nombre del Invitado</label>
              <Input
                value={newGuest.name}
                onChange={(e) => setNewGuest({ ...newGuest, name: e.target.value })}
                placeholder="Nombre completo"
                className="input-dark"
                data-testid="guest-name-input"
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Teléfono (opcional)</label>
              <Input
                value={newGuest.phone}
                onChange={(e) => setNewGuest({ ...newGuest, phone: e.target.value })}
                placeholder="+1 234 567 890"
                className="input-dark"
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Válido por</label>
              <Select value={newGuest.valid_days} onValueChange={(v) => setNewGuest({ ...newGuest, valid_days: v })}>
                <SelectTrigger className="bg-zinc-800 border-zinc-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-700">
                  <SelectItem value="1">1 día</SelectItem>
                  <SelectItem value="3">3 días</SelectItem>
                  <SelectItem value="7">1 semana</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleCreateGuest} className="w-full btn-gym-primary" data-testid="save-guest-btn">
              <Check size={20} className="mr-2" />
              Crear Pase
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Active Guests */}
      {activeGuests.length > 0 && (
        <div>
          <h2 className="font-bold mb-3 flex items-center gap-2">
            <Users size={18} />
            Pases Activos
          </h2>
          <div className="space-y-3">
            {activeGuests.map((guest, index) => (
              <motion.div
                key={guest.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="stat-card"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg"
                      style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
                    >
                      {guest.name?.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-bold">{guest.name}</h3>
                      <code className="text-xs bg-zinc-800 px-2 py-0.5 rounded">{guest.code}</code>
                    </div>
                  </div>
                  {getStatusBadge(guest)}
                </div>

                <div className="flex items-center gap-4 text-sm text-zinc-400 mb-4">
                  <div className="flex items-center gap-1">
                    <Clock size={14} />
                    <span>Válido hasta: {formatDateTime(guest.valid_until)}</span>
                  </div>
                </div>

                <Button
                  onClick={() => showGuestQR(guest)}
                  className="w-full bg-zinc-800 hover:bg-zinc-700 text-white"
                  data-testid={`show-qr-${guest.code}`}
                >
                  <QrCode size={18} className="mr-2" />
                  Mostrar QR del Invitado
                </Button>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* All Guests History */}
      {guests.length > activeGuests.length && (
        <div>
          <h2 className="font-bold mb-3 text-zinc-400">Historial</h2>
          <div className="space-y-2">
            {guests.filter(g => !activeGuests.includes(g)).map((guest) => (
              <div key={guest.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm">
                    {guest.name?.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium text-zinc-400">{guest.name}</p>
                    <p className="text-xs text-zinc-600">{formatDate(guest.created_at)}</p>
                  </div>
                </div>
                {getStatusBadge(guest)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {guests.length === 0 && !loading && (
        <div className="text-center py-8">
          <Users size={48} className="mx-auto text-zinc-700 mb-4" />
          <p className="text-zinc-500">No has creado pases de invitado</p>
          <p className="text-zinc-600 text-sm">Crea uno para traer amigos al gimnasio</p>
        </div>
      )}

      {/* Guest QR Modal */}
      <AnimatePresence>
        {showQRModal && selectedGuest && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black z-50 flex flex-col items-center justify-center p-6"
            onClick={() => setShowQRModal(false)}
          >
            <button
              onClick={() => setShowQRModal(false)}
              className="absolute top-6 right-6 p-3 rounded-full bg-zinc-800"
            >
              <X size={24} />
            </button>

            <div className="text-center mb-8">
              <h2 className="text-xl font-bold">{selectedGuest.name}</h2>
              <p className="text-zinc-400">Invitado de {member?.name}</p>
              <p className="text-sm text-zinc-500 mt-1">Código: {selectedGuest.code}</p>
            </div>

            <div onClick={(e) => e.stopPropagation()} className="bg-white p-6 rounded-2xl">
              {guestQR ? (
                <QRCodeSVG
                  value={guestQR.qr_code}
                  size={250}
                  level="H"
                  includeMargin={false}
                  bgColor="#FFFFFF"
                  fgColor="#000000"
                />
              ) : (
                <div className="w-[250px] h-[250px] bg-zinc-200 animate-pulse rounded" />
              )}
            </div>

            <div className="mt-6 text-center">
              <p className="text-zinc-500 text-sm">Muestra este código en el escáner</p>
              <p className="font-mono text-lg mt-1" style={{ color: 'var(--gym-primary)' }}>
                Actualiza en {countdown}s
              </p>
            </div>

            <div className="mt-6 p-4 bg-zinc-800/50 rounded-xl max-w-sm">
              <p className="text-sm text-zinc-400 text-center">
                Válido hasta: {formatDateTime(selectedGuest.valid_until)}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
