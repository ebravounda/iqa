import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { formatDate, formatDateTime } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Switch } from '../../components/ui/switch';
import { 
  UserPlus, Users, Search, Clock, Check, X, Eye
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminGuests() {
  const { admin } = useAuth();
  const [guests, setGuests] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [permissionData, setPermissionData] = useState({
    can_bring_guests: false,
    max_guests_per_month: 2
  });

  useEffect(() => {
    fetchGuests();
    fetchMembers();
  }, []);

  const fetchGuests = async () => {
    try {
      const response = await axios.get(`${API}/guests`);
      setGuests(response.data);
    } catch (error) {
      console.error('Error fetching guests:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`${API}/members`);
      setMembers(response.data);
    } catch (error) {
      console.error('Error fetching members:', error);
    }
  };

  const handleUpdatePermission = async () => {
    if (!selectedMember) return;
    
    try {
      await axios.put(
        `${API}/members/${selectedMember.id}/guest-permission?can_bring_guests=${permissionData.can_bring_guests}&max_guests_per_month=${permissionData.max_guests_per_month}`
      );
      toast.success('Permiso actualizado');
      setShowPermissionModal(false);
      fetchMembers();
    } catch (error) {
      toast.error('Error al actualizar permiso');
    }
  };

  const openPermissionModal = (member) => {
    setSelectedMember(member);
    setPermissionData({
      can_bring_guests: member.can_bring_guests || false,
      max_guests_per_month: member.max_guests_per_month || 2
    });
    setShowPermissionModal(true);
  };

  const getStatusBadge = (guest) => {
    const now = new Date();
    const validUntil = new Date(guest.valid_until);
    
    if (guest.status === 'expired' || validUntil < now) {
      return <span className="badge badge-danger">Expirado</span>;
    }
    if (guest.status === 'used') {
      return <span className="badge badge-warning">Usado</span>;
    }
    return <span className="badge badge-success">Activo</span>;
  };

  const filteredGuests = guests.filter(g =>
    g.name?.toLowerCase().includes(search.toLowerCase()) ||
    g.code?.toLowerCase().includes(search.toLowerCase()) ||
    g.invited_by_name?.toLowerCase().includes(search.toLowerCase())
  );

  // Members with guest permission
  const membersWithPermission = members.filter(m => m.can_bring_guests);

  return (
    <div className="space-y-6" data-testid="admin-guests">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Invitados</h1>
          <p className="text-zinc-400 text-sm">{guests.length} pases de invitado</p>
        </div>
      </div>

      {/* Members with Guest Permission */}
      <div className="stat-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold flex items-center gap-2">
            <Users size={18} />
            Socios con Permiso de Invitados
          </h3>
          <span className="text-sm text-zinc-400">{membersWithPermission.length} socios</span>
        </div>
        
        <div className="space-y-2">
          {membersWithPermission.length === 0 ? (
            <p className="text-zinc-500 text-sm py-4 text-center">
              Ningún socio tiene permiso para traer invitados
            </p>
          ) : (
            membersWithPermission.map((member) => (
              <div key={member.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-bold">
                    {member.name?.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium">{member.name}</p>
                    <p className="text-xs text-zinc-500">
                      Máx. {member.max_guests_per_month || 2} invitados/mes
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openPermissionModal(member)}
                  className="text-zinc-400"
                >
                  Editar
                </Button>
              </div>
            ))
          )}
        </div>

        <div className="mt-4 pt-4 border-t border-zinc-700">
          <p className="text-sm text-zinc-400 mb-3">Agregar permiso a un socio:</p>
          <div className="flex flex-wrap gap-2">
            {members.filter(m => !m.can_bring_guests && m.status === 'active').slice(0, 5).map((member) => (
              <button
                key={member.id}
                onClick={() => openPermissionModal(member)}
                className="flex items-center gap-2 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors"
              >
                <UserPlus size={14} />
                {member.name}
              </button>
            ))}
            {members.filter(m => !m.can_bring_guests && m.status === 'active').length > 5 && (
              <span className="text-zinc-500 text-sm py-2">
                +{members.filter(m => !m.can_bring_guests && m.status === 'active').length - 5} más
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar invitados..."
          className="input-dark pl-10"
        />
      </div>

      {/* Guests Table */}
      <div className="stat-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Invitado</th>
                <th>Código</th>
                <th>Invitado por</th>
                <th>Válido hasta</th>
                <th>Accesos</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8">
                    <div className="skeleton h-4 w-32 mx-auto" />
                  </td>
                </tr>
              ) : filteredGuests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-zinc-500 py-8">
                    No hay pases de invitado registrados
                  </td>
                </tr>
              ) : (
                filteredGuests.map((guest) => (
                  <tr key={guest.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-500 font-bold text-sm">
                          {guest.name?.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium">{guest.name}</p>
                          {guest.phone && (
                            <p className="text-xs text-zinc-500">{guest.phone}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <code className="text-sm bg-amber-500/10 text-amber-400 px-2 py-1 rounded font-mono">
                        {guest.code}
                      </code>
                    </td>
                    <td className="text-zinc-400">{guest.invited_by_name}</td>
                    <td className="text-zinc-400 text-sm">{formatDateTime(guest.valid_until)}</td>
                    <td className="text-center">{guest.accesses}</td>
                    <td>{getStatusBadge(guest)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Permission Modal */}
      <Dialog open={showPermissionModal} onOpenChange={setShowPermissionModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle>Permiso de Invitados</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {selectedMember && (
              <>
                <div className="flex items-center gap-3 p-3 bg-zinc-800 rounded-lg">
                  <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center font-bold">
                    {selectedMember.name?.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium">{selectedMember.name}</p>
                    <p className="text-sm text-zinc-500">{selectedMember.code}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-zinc-800 rounded-lg">
                  <div>
                    <p className="font-medium">Puede traer invitados</p>
                    <p className="text-sm text-zinc-500">Permitir crear pases de invitado</p>
                  </div>
                  <Switch
                    checked={permissionData.can_bring_guests}
                    onCheckedChange={(checked) => setPermissionData({ ...permissionData, can_bring_guests: checked })}
                  />
                </div>

                {permissionData.can_bring_guests && (
                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Máximo invitados por mes</label>
                    <Input
                      type="number"
                      min={1}
                      max={10}
                      value={permissionData.max_guests_per_month}
                      onChange={(e) => setPermissionData({ ...permissionData, max_guests_per_month: parseInt(e.target.value) || 2 })}
                      className="input-dark"
                    />
                  </div>
                )}

                <Button onClick={handleUpdatePermission} className="w-full btn-gym-primary">
                  <Check size={20} className="mr-2" />
                  Guardar Cambios
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
