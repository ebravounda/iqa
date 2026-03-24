import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getDevices, createDevice, getGym } from '../../lib/api';
import { formatDateTime } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Plus, Cpu, Copy, RefreshCw, Check, Wifi, WifiOff } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminDevices() {
  const { admin, isSuperAdmin } = useAuth();
  const [devices, setDevices] = useState([]);
  const [gym, setGym] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDevice, setNewDevice] = useState({ name: '', location: '' });
  const [copiedToken, setCopiedToken] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const gymId = admin?.gym_id;
      const [devicesRes, gymRes] = await Promise.all([
        getDevices(isSuperAdmin ? null : gymId),
        gymId ? getGym(gymId) : Promise.resolve({ data: null })
      ]);
      setDevices(devicesRes.data);
      setGym(gymRes.data);
    } catch (error) {
      console.error('Error fetching devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDevice = async () => {
    if (!newDevice.name) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      const gymId = admin?.gym_id;
      await createDevice({ ...newDevice, gym_id: gymId });
      toast.success('Dispositivo registrado');
      setShowCreateModal(false);
      setNewDevice({ name: '', location: '' });
      fetchData();
    } catch (error) {
      toast.error('Error al registrar dispositivo');
    }
  };

  const copyToken = () => {
    if (gym?.api_token) {
      navigator.clipboard.writeText(gym.api_token);
      setCopiedToken(true);
      toast.success('Token copiado al portapapeles');
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  const isOnline = (lastPing) => {
    if (!lastPing) return false;
    const diff = Date.now() - new Date(lastPing).getTime();
    return diff < 5 * 60 * 1000; // 5 minutes
  };

  return (
    <div className="space-y-6" data-testid="admin-devices">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Dispositivos Raspberry Pi</h1>
          <p className="text-zinc-400 text-sm">{devices.length} dispositivos registrados</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button className="btn-gym-primary" data-testid="add-device-btn">
              <Plus size={20} className="mr-2" />
              Agregar Dispositivo
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle>Registrar Nuevo Dispositivo</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Nombre</label>
                <Input
                  value={newDevice.name}
                  onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                  placeholder="Ej: Raspberry Pi Entrada"
                  className="input-dark"
                  data-testid="device-name-input"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-1 block">Ubicación (opcional)</label>
                <Input
                  value={newDevice.location}
                  onChange={(e) => setNewDevice({ ...newDevice, location: e.target.value })}
                  placeholder="Ej: Entrada principal"
                  className="input-dark"
                />
              </div>
              <Button onClick={handleCreateDevice} className="w-full btn-gym-primary" data-testid="save-device-btn">
                <Cpu size={20} className="mr-2" />
                Registrar Dispositivo
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* API Token Card */}
      {gym && (
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
              <Cpu size={20} className="text-amber-500" />
            </div>
            <div>
              <h3 className="font-bold">Token de API del Gimnasio</h3>
              <p className="text-xs text-zinc-500">Usa este token en tu Raspberry Pi</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-zinc-800 px-4 py-3 rounded-lg font-mono text-sm text-zinc-300 overflow-x-auto">
              {gym.api_token}
            </code>
            <Button
              onClick={copyToken}
              variant="outline"
              className="border-zinc-700 shrink-0"
              data-testid="copy-token-btn"
            >
              {copiedToken ? <Check size={18} /> : <Copy size={18} />}
            </Button>
          </div>
        </div>
      )}

      {/* Devices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          [1, 2].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-6 w-32 mb-4" />
              <div className="skeleton h-4 w-24" />
            </div>
          ))
        ) : devices.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Cpu size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-zinc-500">No hay dispositivos registrados</p>
            <p className="text-zinc-600 text-sm">Agrega tu primera Raspberry Pi</p>
          </div>
        ) : (
          devices.map((device) => (
            <div key={device.id} className="stat-card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    isOnline(device.last_ping) ? 'bg-emerald-500/10' : 'bg-zinc-800'
                  }`}>
                    <Cpu size={20} className={isOnline(device.last_ping) ? 'text-emerald-500' : 'text-zinc-500'} />
                  </div>
                  <div>
                    <h3 className="font-bold">{device.name}</h3>
                    {device.location && (
                      <p className="text-xs text-zinc-500">{device.location}</p>
                    )}
                  </div>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
                  isOnline(device.last_ping) 
                    ? 'bg-emerald-500/10 text-emerald-500' 
                    : 'bg-zinc-800 text-zinc-500'
                }`}>
                  {isOnline(device.last_ping) ? (
                    <>
                      <Wifi size={12} />
                      Online
                    </>
                  ) : (
                    <>
                      <WifiOff size={12} />
                      Offline
                    </>
                  )}
                </div>
              </div>
              
              <div className="text-sm text-zinc-400">
                <p>ID: <code className="bg-zinc-800 px-2 py-0.5 rounded text-xs">{device.id.slice(0, 8)}...</code></p>
                {device.last_ping && (
                  <p className="mt-1">Último ping: {formatDateTime(device.last_ping)}</p>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Setup Instructions */}
      <div className="stat-card">
        <h3 className="font-bold text-lg mb-4">Instrucciones de Configuración</h3>
        <div className="space-y-4 text-sm text-zinc-400">
          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">1</span>
            <div>
              <p className="font-medium text-white mb-1">Descarga el script para Raspberry Pi</p>
              <code className="block bg-zinc-800 p-3 rounded-lg text-xs">
                wget https://tu-servidor.com/raspberry/setup.py
              </code>
            </div>
          </div>
          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">2</span>
            <div>
              <p className="font-medium text-white mb-1">Configura el token de API</p>
              <code className="block bg-zinc-800 p-3 rounded-lg text-xs">
                GYM_TOKEN="{gym?.api_token?.slice(0, 20)}..."
              </code>
            </div>
          </div>
          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">3</span>
            <div>
              <p className="font-medium text-white mb-1">Conecta los relés a GPIO 17 (entrada) y GPIO 27 (salida)</p>
              <p>Consulta la documentación completa para el diagrama de conexión.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">4</span>
            <div>
              <p className="font-medium text-white mb-1">Ejecuta el script</p>
              <code className="block bg-zinc-800 p-3 rounded-lg text-xs">
                python3 setup.py
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
