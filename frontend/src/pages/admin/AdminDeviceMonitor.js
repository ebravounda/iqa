import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';
import { Cpu, Wifi, WifiOff, RefreshCw, RotateCcw, Download, Play, Thermometer, HardDrive, Clock, Globe, MapPin } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminDeviceMonitor() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState({});

  const fetchDevices = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/devices/status`);
      setDevices(res.data);
    } catch { toast.error('Error al cargar dispositivos'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchDevices(); const i = setInterval(fetchDevices, 30000); return () => clearInterval(i); }, [fetchDevices]);

  const sendCommand = async (deviceId, command, label) => {
    if (!window.confirm(`Enviar comando "${label}" a este dispositivo?`)) return;
    setSending(p => ({ ...p, [deviceId]: command }));
    try {
      await axios.post(`${API}/devices/${deviceId}/command`, { command });
      toast.success(`Comando "${label}" enviado`);
      setTimeout(fetchDevices, 2000);
    } catch (err) { toast.error(err.response?.data?.detail || 'Error'); }
    finally { setSending(p => ({ ...p, [deviceId]: null })); }
  };

  const formatTime = (iso) => {
    if (!iso) return 'Nunca';
    const d = new Date(iso);
    return d.toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatUptime = (seconds) => {
    if (!seconds) return '-';
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}d ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6" data-testid="device-monitor-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Monitor de Dispositivos</h1>
          <p className="text-zinc-400 text-sm">Estado en tiempo real de tus Raspberry Pi</p>
        </div>
        <Button onClick={fetchDevices} variant="outline" size="sm" className="border-zinc-700 text-zinc-300" data-testid="refresh-devices-btn">
          <RefreshCw size={16} className="mr-2" /> Actualizar
        </Button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-emerald-500/10 border border-zinc-800 rounded-xl p-4 text-center">
          <Wifi size={24} className="mx-auto text-emerald-500 mb-1" />
          <p className="text-2xl font-bold text-emerald-500">{devices.filter(d => d.computed_status === 'online').length}</p>
          <p className="text-xs text-zinc-400">Online</p>
        </div>
        <div className="bg-red-500/10 border border-zinc-800 rounded-xl p-4 text-center">
          <WifiOff size={24} className="mx-auto text-red-500 mb-1" />
          <p className="text-2xl font-bold text-red-500">{devices.filter(d => d.computed_status === 'offline').length}</p>
          <p className="text-xs text-zinc-400">Offline</p>
        </div>
        <div className="bg-zinc-800 border border-zinc-800 rounded-xl p-4 text-center">
          <Cpu size={24} className="mx-auto text-zinc-400 mb-1" />
          <p className="text-2xl font-bold text-zinc-300">{devices.length}</p>
          <p className="text-xs text-zinc-400">Total</p>
        </div>
      </div>

      {/* Devices */}
      {devices.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <Cpu size={48} className="mx-auto mb-4" />
          <p>No hay dispositivos registrados</p>
        </div>
      ) : (
        <div className="space-y-4">
          {devices.map((d) => (
            <div key={d.id} className={`border rounded-xl p-5 transition-all ${d.computed_status === 'online' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'}`} data-testid={`device-card-${d.id}`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${d.computed_status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                  <div>
                    <h3 className="font-bold text-lg">{d.name || 'Dispositivo'}</h3>
                    <p className="text-zinc-400 text-sm">{d.gym_name} {d.location ? `- ${d.location}` : ''}</p>
                  </div>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${d.computed_status === 'online' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {d.computed_status === 'online' ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>

              {/* Info Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <InfoItem icon={Globe} label="IP Publica" value={d.ip_address || '-'} />
                <InfoItem icon={MapPin} label="IP Local" value={d.local_ip || '-'} />
                <InfoItem icon={Clock} label="Ultimo ping" value={formatTime(d.last_ping)} />
                <InfoItem icon={Clock} label="Uptime" value={formatUptime(d.uptime)} />
                {d.cpu_temp && <InfoItem icon={Thermometer} label="Temp CPU" value={`${d.cpu_temp}°C`} warn={d.cpu_temp > 70} />}
                {d.cpu_usage !== undefined && d.cpu_usage !== null && <InfoItem icon={Cpu} label="CPU" value={`${d.cpu_usage}%`} warn={d.cpu_usage > 80} />}
                {d.memory_usage !== undefined && d.memory_usage !== null && <InfoItem icon={HardDrive} label="RAM" value={`${d.memory_usage}%`} warn={d.memory_usage > 85} />}
                {d.software_version && <InfoItem icon={Cpu} label="Version" value={d.software_version} />}
              </div>

              {/* Commands */}
              <div className="flex gap-2 flex-wrap">
                <Button onClick={() => sendCommand(d.id, 'reboot', 'Reiniciar')} disabled={sending[d.id] === 'reboot'} variant="outline" size="sm" className="border-amber-700 text-amber-400 hover:bg-amber-500/10" data-testid={`reboot-${d.id}`}>
                  <RotateCcw size={14} className="mr-1" /> {sending[d.id] === 'reboot' ? 'Enviando...' : 'Reiniciar'}
                </Button>
                <Button onClick={() => sendCommand(d.id, 'update', 'Actualizar')} disabled={sending[d.id] === 'update'} variant="outline" size="sm" className="border-blue-700 text-blue-400 hover:bg-blue-500/10" data-testid={`update-${d.id}`}>
                  <Download size={14} className="mr-1" /> {sending[d.id] === 'update' ? 'Enviando...' : 'Actualizar'}
                </Button>
                <Button onClick={() => sendCommand(d.id, 'restart_service', 'Reiniciar servicio')} disabled={sending[d.id] === 'restart_service'} variant="outline" size="sm" className="border-purple-700 text-purple-400 hover:bg-purple-500/10" data-testid={`restart-svc-${d.id}`}>
                  <Play size={14} className="mr-1" /> {sending[d.id] === 'restart_service' ? 'Enviando...' : 'Reiniciar Servicio'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InfoItem({ icon: Icon, label, value, warn }) {
  return (
    <div className="bg-zinc-900/50 rounded-lg p-2">
      <div className="flex items-center gap-1 mb-1">
        <Icon size={12} className="text-zinc-500" />
        <span className="text-[10px] text-zinc-500 uppercase">{label}</span>
      </div>
      <p className={`text-sm font-mono truncate ${warn ? 'text-amber-400' : 'text-zinc-300'}`}>{value}</p>
    </div>
  );
}
