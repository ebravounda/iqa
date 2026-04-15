import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getDevices, createDevice, deleteDevice, getGym, getGyms } from '../../lib/api';
import { formatDateTime } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Plus, Cpu, Copy, RefreshCw, Check, Wifi, WifiOff, Trash2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';

export default function AdminDevices() {
  const { admin, isSuperAdmin } = useAuth();
  const isSA = isSuperAdmin || admin?.role === 'super_admin' || admin?.original_role === 'super_admin';
  const [devices, setDevices] = useState([]);
  const [inactiveDevices, setInactiveDevices] = useState([]);
  const [gym, setGym] = useState(null);
  const [gyms, setGyms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDevice, setNewDevice] = useState({ name: '', location: '', gym_id: admin?.gym_id || '' });
  const [copiedToken, setCopiedToken] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const gymId = admin?.gym_id;
      const [devicesRes] = await Promise.all([
        getDevices(isSA ? null : gymId)
      ]);
      const res = devicesRes.data;
      setDevices(res.active || res);
      setInactiveDevices(res.inactive || []);
      
      if (isSA) {
        const gymsRes = await getGyms();
        setGyms(gymsRes.data);
        if (gymId) {
          // Impersonating - load that gym
          setNewDevice(prev => ({ ...prev, gym_id: gymId }));
          const gymRes = await getGym(gymId);
          setGym(gymRes.data);
          const devFiltered = await getDevices(gymId);
          const resF = devFiltered.data;
          setDevices(resF.active || resF);
          setInactiveDevices(resF.inactive || []);
        } else if (gymsRes.data.length > 0 && !newDevice.gym_id) {
          setNewDevice(prev => ({ ...prev, gym_id: gymsRes.data[0].id }));
          const gymRes = await getGym(gymsRes.data[0].id);
          setGym(gymRes.data);
        }
      } else if (gymId) {
        const gymRes = await getGym(gymId);
        setGym(gymRes.data);
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGymChange = async (gymId) => {
    setNewDevice(prev => ({ ...prev, gym_id: gymId }));
    try {
      const gymRes = await getGym(gymId);
      setGym(gymRes.data);
      // Reload devices for this gym
      const devicesRes = await getDevices(gymId);
      const res = devicesRes.data;
      setDevices(res.active || res);
      setInactiveDevices(res.inactive || []);
    } catch (error) {
      console.error('Error fetching gym:', error);
    }
  };

  const handleCreateDevice = async () => {
    if (!newDevice.name) {
      toast.error('El nombre es requerido');
      return;
    }

    const gymId = admin?.gym_id || newDevice.gym_id;
    if (!gymId) {
      toast.error('Selecciona un gimnasio');
      return;
    }

    try {
      await createDevice({ ...newDevice, gym_id: gymId });
      toast.success('Dispositivo registrado');
      setShowCreateModal(false);
      setNewDevice({ name: '', location: '', gym_id: gymId });
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

  const handleDeleteDevice = async (deviceId) => {
    if (!window.confirm('¿Estás seguro de eliminar este dispositivo?')) return;
    try {
      await deleteDevice(deviceId);
      toast.success('Dispositivo eliminado');
      fetchData();
    } catch (error) {
      toast.error('Error al eliminar dispositivo');
    }
  };

  return (
    <div className="space-y-6 pb-12" style={{ overflowY: 'auto' }} data-testid="admin-devices">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Dispositivos Raspberry Pi</h1>
          <p className="text-zinc-400 text-sm">{devices.length} dispositivos registrados{gym ? ` - ${gym.name}` : ''}</p>
        </div>
        
        <div className="flex items-center gap-3">
          {isSA && gyms.length > 0 && (
            <Select value={newDevice.gym_id} onValueChange={handleGymChange}>
              <SelectTrigger className="w-[220px] bg-zinc-800 border-zinc-700" data-testid="gym-selector">
                <SelectValue placeholder="Seleccionar gimnasio" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {gyms.map((g) => (
                  <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        
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
              {isSA && (
                <div>
                  <label className="text-sm text-zinc-400 mb-1 block">Gimnasio</label>
                  <Select value={newDevice.gym_id} onValueChange={handleGymChange}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="device-gym-select">
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
              
              <div className="text-sm text-zinc-400 space-y-2">
                <div className="flex items-center gap-2">
                  <span>ID:</span>
                  <code className="bg-zinc-800 px-2 py-0.5 rounded text-xs flex-1 overflow-x-auto">{device.id}</code>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 shrink-0" data-testid={`copy-device-id-${device.id}`}
                    onClick={() => { navigator.clipboard.writeText(device.id); toast.success('Device ID copiado'); }}>
                    <Copy size={14} />
                  </Button>
                </div>
                {device.last_ping && (
                  <p>Último ping: {formatDateTime(device.last_ping)}</p>
                )}
              </div>
              <div className="mt-4 pt-3 border-t border-zinc-800">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteDevice(device.id)}
                  className="text-red-500 hover:text-red-400 hover:bg-red-500/10 w-full justify-center"
                  data-testid={`delete-device-${device.id}`}
                >
                  <Trash2 size={16} className="mr-2" />
                  Desactivar Dispositivo
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Inactive Devices - Last 8 */}
      {inactiveDevices.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-zinc-500 mb-3">Dispositivos Desactivados (ultimos 8)</h3>
          <div className="space-y-2">
            {inactiveDevices.map((device) => (
              <div key={device.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50 opacity-60">
                <div className="flex items-center gap-3">
                  <Cpu size={16} className="text-zinc-600" />
                  <div>
                    <span className="text-sm text-zinc-400">{device.name}</span>
                    {device.location && <span className="text-xs text-zinc-600 ml-2">({device.location})</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-600">{device.deactivated_at ? new Date(device.deactivated_at).toLocaleDateString() : ''}</span>
                  <Button variant="ghost" size="sm" className="h-7 text-red-500/50 hover:text-red-400 hover:bg-red-500/10 text-xs"
                    onClick={() => { deleteDevice(device.id).then(() => { toast.success('Eliminado permanentemente'); fetchData(); }); }}
                    data-testid={`delete-inactive-${device.id}`}>
                    <Trash2 size={12} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Setup Instructions - Solo Super Admin */}
      {isSA && (
      <div className="stat-card">
        <h3 className="font-bold text-lg mb-4">Guia de Configuracion - Raspberry Pi</h3>
        <div className="space-y-5 text-sm text-zinc-400">
          
          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">1</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Instalar Raspberry Pi OS en la MicroSD</p>
              <p className="mb-2">Descarga <a href="https://www.raspberrypi.com/software/" target="_blank" rel="noreferrer" className="text-emerald-400 underline">Raspberry Pi Imager</a> en tu PC.</p>
              <div className="bg-zinc-800/50 p-3 rounded-lg space-y-1 text-xs">
                <p>Dispositivo: <span className="text-white">Raspberry Pi 3/4/5</span></p>
                <p>Sistema: <span className="text-white">Raspberry Pi OS Lite (64-bit)</span></p>
                <p>Click engranaje: Hostname: <span className="text-white">gymaccess</span>, SSH: <span className="text-white">activado</span>, Usuario: <span className="text-white">pi</span>, WiFi: configurar</p>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">2</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Conexiones de los reles (GPIO)</p>
              <div className="bg-zinc-800/50 p-3 rounded-lg font-mono text-xs space-y-1">
                <p><span className="text-red-400">Pin 2  (5V)</span>      &rarr; VCC del modulo rele</p>
                <p><span className="text-zinc-300">Pin 6  (GND)</span>     &rarr; GND del modulo rele</p>
                <p><span className="text-emerald-400">Pin 32 (GPIO12)</span>  &rarr; IN1 (Torno ENTRADA)</p>
                <p><span className="text-blue-400">Pin 36 (GPIO16)</span>  &rarr; IN2 (Torno SALIDA)</p>
              </div>
              <p className="mt-2 text-xs">Usa terminales <span className="text-white">NO</span> (Normally Open) y <span className="text-white">COM</span> del rele hacia el torno.</p>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">3</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Conectar por SSH</p>
              <p className="mb-2">Inserta la MicroSD, conecta ethernet/WiFi y alimentacion. Espera 2 minutos.</p>
              <code className="block bg-zinc-800 p-3 rounded-lg text-xs text-emerald-400">
                ssh pi@gymaccess.local
              </code>
              <p className="mt-2 text-xs text-zinc-500">Si no resuelve, usa la IP directa: ssh pi@192.168.1.X</p>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">4</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Instalar dependencias</p>
              <div className="bg-zinc-800 p-3 rounded-lg text-xs space-y-2 font-mono">
                <p className="text-emerald-400">sudo apt update && sudo apt upgrade -y</p>
                <p className="text-emerald-400">sudo apt install -y python3-pip python3-venv python3-lgpio swig</p>
                <p className="text-emerald-400">python3 -m venv ~/gymaccess-env</p>
                <p className="text-emerald-400">source ~/gymaccess-env/bin/activate</p>
                <p className="text-emerald-400">pip install requests python-dotenv evdev gpiozero</p>
                <p className="text-zinc-500"># Enlazar lgpio del sistema al venv:</p>
                <p className="text-emerald-400">ln -s /usr/lib/python3/dist-packages/lgpio* ~/gymaccess-env/lib/python3.*/site-packages/</p>
                <p className="text-emerald-400">ln -s /usr/lib/python3/dist-packages/_lgpio* ~/gymaccess-env/lib/python3.*/site-packages/</p>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">5</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Crear el script de control de acceso</p>
              <div className="bg-zinc-800 p-3 rounded-lg text-xs space-y-2 font-mono">
                <p className="text-emerald-400">mkdir -p ~/gymaccess && cd ~/gymaccess</p>
                <p className="text-emerald-400">nano access_control.py</p>
              </div>
              <p className="mt-2">Pega el contenido del script de control de acceso v2.1 (solicitar a soporte).</p>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">6</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Configurar Token y Device ID</p>
              <p className="mb-2">Copia el <span className="text-white">Token de API</span> del gym y el <span className="text-white">Device ID</span> del dispositivo creado arriba.</p>
              {gym?.api_token && (
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs">Token API:</span>
                  <code className="bg-zinc-800 px-2 py-0.5 rounded text-xs flex-1 overflow-x-auto text-amber-400">{gym.api_token.slice(0, 25)}...</code>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 shrink-0" data-testid="copy-api-token"
                    onClick={() => { navigator.clipboard.writeText(gym.api_token); toast.success('Token copiado'); }}>
                    <Copy size={14} />
                  </Button>
                </div>
              )}
              <div className="bg-zinc-800 p-3 rounded-lg text-xs font-mono">
                <p className="text-zinc-500 mb-1"># Crear archivo .env en la Raspberry:</p>
                <p className="text-emerald-400">nano ~/gymaccess/.env</p>
                <p className="text-zinc-500 mt-2"># Contenido:</p>
                <p className="text-amber-400">GYMACCESS_SERVER_URL=https://c.ingresoqr.com</p>
                <p className="text-amber-400">GYMACCESS_GYM_TOKEN=<span className="text-white">PEGA_TU_TOKEN_DEL_GYM</span></p>
                <p className="text-amber-400">GYMACCESS_DEVICE_ID=<span className="text-white">PEGA_TU_DEVICE_ID</span></p>
                <p className="text-amber-400">GYMACCESS_QR_MODE=usb</p>
              </div>
              <p className="mt-2 text-xs text-red-400">IMPORTANTE: Cada gym tiene su propio Token. No reutilices tokens entre gyms.</p>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">7</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Probar el sistema</p>
              <div className="bg-zinc-800 p-3 rounded-lg text-xs font-mono">
                <p className="text-emerald-400">sudo touch /var/log/gymaccess.log && sudo chown pi:pi /var/log/gymaccess.log</p>
                <p className="text-emerald-400">sudo ~/gymaccess-env/bin/python3 ~/gymaccess/access_control.py</p>
              </div>
              <p className="mt-2">Debe mostrar "GPIO: ACTIVO" y "HEARTBEAT OK". Escanea un QR de un socio con el lector USB.</p>
            </div>
          </div>

          <div className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold">8</span>
            <div className="flex-1">
              <p className="font-medium text-white mb-2">Arranque automatico (servicio systemd)</p>
              <div className="bg-zinc-800 p-3 rounded-lg text-xs font-mono space-y-2">
                <p className="text-zinc-500"># Crear servicio:</p>
                <p className="text-emerald-400">sudo bash -c 'cat &gt; /etc/systemd/system/gymaccess.service &lt;&lt; EOF</p>
                <p className="text-amber-400">[Unit]</p>
                <p className="text-amber-400">Description=IngresoQR Access Control</p>
                <p className="text-amber-400">After=network.target</p>
                <p className="text-amber-400">[Service]</p>
                <p className="text-amber-400">ExecStart=/home/pi/gymaccess-env/bin/python3 /home/pi/gymaccess/access_control.py</p>
                <p className="text-amber-400">WorkingDirectory=/home/pi/gymaccess</p>
                <p className="text-amber-400">User=root</p>
                <p className="text-amber-400">Restart=always</p>
                <p className="text-amber-400">RestartSec=5</p>
                <p className="text-amber-400">[Install]</p>
                <p className="text-amber-400">WantedBy=multi-user.target</p>
                <p className="text-emerald-400">EOF'</p>
                <p className="text-zinc-500 mt-2"># Activar e iniciar:</p>
                <p className="text-emerald-400">sudo systemctl daemon-reload</p>
                <p className="text-emerald-400">sudo systemctl enable gymaccess.service</p>
                <p className="text-emerald-400">sudo systemctl start gymaccess.service</p>
                <p className="text-emerald-400">sudo systemctl status gymaccess.service</p>
              </div>
            </div>
          </div>

          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
            <p className="text-emerald-400 font-medium">Listo! La Raspberry arrancara automaticamente al encender y controlara el torno.</p>
            <p className="text-xs text-zinc-400 mt-1">El dispositivo aparecera como "Online" en el panel y enviara heartbeat cada 60 segundos.</p>
            <p className="text-xs text-zinc-500 mt-1">Comandos utiles: <code className="bg-zinc-800 px-1 rounded">sudo systemctl status gymaccess</code> | <code className="bg-zinc-800 px-1 rounded">sudo journalctl -u gymaccess -f</code></p>
          </div>

        </div>
      </div>
      )}
    </div>
  );
}
