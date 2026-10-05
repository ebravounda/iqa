import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Unlock, LogIn, LogOut, Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Quick-action buttons for admins to remotely open the gym turnstile.
 * Shows "Abrir entrada" and "Abrir salida" (bidirectional turnstile support).
 * The Raspberry Pi picks up the command on its next heartbeat (every ~5s).
 */
export default function OpenTurnstileButton({ gymId }) {
  const [devices, setDevices] = useState([]);
  const [sending, setSending] = useState(null); // 'entry' | 'exit' | null
  const [picker, setPicker] = useState(null);   // { direction } when multiple devices

  useEffect(() => {
    if (!gymId) return;
    const params = new URLSearchParams();
    params.set('gym_id', gymId);
    axios.get(`${API}/devices?${params.toString()}`)
      .then(r => {
        const list = Array.isArray(r.data) ? r.data : (r.data?.active || []);
        setDevices(list.filter(d => d.active !== false));
      })
      .catch(() => setDevices([]));
  }, [gymId]);

  const sendCmd = async (deviceId, direction) => {
    const command = direction === 'exit' ? 'open_turnstile_exit' : 'open_turnstile';
    try {
      setSending(direction);
      await axios.post(`${API}/devices/${deviceId}/command`, { command });
      toast.success(`Abriendo ${direction === 'exit' ? 'salida' : 'entrada'}...`);
      setPicker(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'No se pudo enviar el comando');
    } finally {
      setSending(null);
    }
  };

  const handleClick = (direction) => {
    if (devices.length === 1) {
      sendCmd(devices[0].id, direction);
    } else {
      setPicker({ direction });
    }
  };

  if (!devices.length) return null;

  return (
    <>
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => handleClick('entry')}
          disabled={!!sending}
          className="flex items-center gap-2 px-3 py-2 rounded-xl font-bold text-sm text-black transition-transform active:scale-95 disabled:opacity-60"
          style={{ backgroundColor: 'var(--gym-primary, #c5f82a)' }}
          data-testid="open-turnstile-entry-btn"
        >
          {sending === 'entry' ? <Loader2 size={16} className="animate-spin" /> : <LogIn size={16} />}
          Abrir entrada
        </button>
        <button
          onClick={() => handleClick('exit')}
          disabled={!!sending}
          className="flex items-center gap-2 px-3 py-2 rounded-xl font-bold text-sm text-white transition-transform active:scale-95 disabled:opacity-60"
          style={{ backgroundColor: '#2563eb' }}
          data-testid="open-turnstile-exit-btn"
        >
          {sending === 'exit' ? <Loader2 size={16} className="animate-spin" /> : <LogOut size={16} />}
          Abrir salida
        </button>
      </div>

      {picker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" data-testid="turnstile-picker-modal">
          <div className="w-full max-w-sm rounded-2xl p-5" style={{ background: 'var(--bg-secondary, #18181b)', border: '1px solid var(--border-primary, #27272a)' }}>
            <h3 className="font-black text-lg mb-1">
              {picker.direction === 'exit' ? 'Abrir SALIDA de...' : 'Abrir ENTRADA de...'}
            </h3>
            <p className="text-xs mb-4" style={{ color: 'var(--text-muted, #71717a)' }}>Selecciona el torno:</p>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {devices.map(d => (
                <button
                  key={d.id}
                  onClick={() => sendCmd(d.id, picker.direction)}
                  disabled={!!sending}
                  className="w-full flex items-center justify-between p-3 rounded-xl text-left hover:bg-zinc-800/60 transition-colors disabled:opacity-50"
                  style={{ background: 'var(--bg-tertiary, #27272a)' }}
                  data-testid={`turnstile-device-${d.id}`}
                >
                  <div>
                    <p className="font-bold text-sm">{d.name}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted, #71717a)' }}>{d.location || 'Sin ubicacion'}</p>
                  </div>
                  <Unlock size={18} style={{ color: 'var(--gym-primary, #c5f82a)' }} />
                </button>
              ))}
            </div>
            <button onClick={() => setPicker(null)} className="w-full mt-4 py-2 text-xs text-zinc-500 hover:text-zinc-300" data-testid="turnstile-picker-close">
              Cancelar
            </button>
          </div>
        </div>
      )}
    </>
  );
}
