import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Unlock, Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Quick-action button for admins to remotely open the gym turnstile.
 * Lists all devices of the admin's gym and lets them send `open_turnstile`
 * which the Raspberry Pi picks up on its next heartbeat (every ~30s).
 */
export default function OpenTurnstileButton({ gymId }) {
  const [devices, setDevices] = useState([]);
  const [sending, setSending] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    if (!gymId) return;
    const params = new URLSearchParams();
    params.set('gym_id', gymId);
    axios.get(`${API}/devices?${params.toString()}`)
      .then(r => {
        // Backend returns { active: [...], inactive: [...] } — use the active list.
        const list = Array.isArray(r.data) ? r.data : (r.data?.active || []);
        setDevices(list.filter(d => d.active !== false));
      })
      .catch(() => setDevices([]));
  }, [gymId]);

  const sendOpen = async (deviceId) => {
    try {
      setSending(true);
      await axios.post(`${API}/devices/${deviceId}/command`, { command: 'open_turnstile' });
      toast.success('Comando enviado. El torno abrira en unos segundos.');
      setShowPicker(false);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'No se pudo enviar el comando');
    } finally {
      setSending(false);
    }
  };

  if (!devices.length) return null;

  // If there's a single device, use a one-tap button; otherwise show picker
  const singleDevice = devices.length === 1 ? devices[0] : null;

  return (
    <>
      <button
        onClick={() => (singleDevice ? sendOpen(singleDevice.id) : setShowPicker(true))}
        disabled={sending}
        className="flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm text-black transition-transform active:scale-95 disabled:opacity-60"
        style={{ backgroundColor: 'var(--gym-primary, #c5f82a)' }}
        data-testid="open-turnstile-btn"
      >
        {sending ? <Loader2 size={16} className="animate-spin" /> : <Unlock size={16} />}
        Abrir torno
      </button>

      {showPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" data-testid="turnstile-picker-modal">
          <div className="w-full max-w-sm rounded-2xl p-5" style={{ background: 'var(--bg-secondary, #18181b)', border: '1px solid var(--border-primary, #27272a)' }}>
            <h3 className="font-black text-lg mb-1">Selecciona un torno</h3>
            <p className="text-xs mb-4" style={{ color: 'var(--text-muted, #71717a)' }}>El dispositivo abrira al recibir el comando.</p>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {devices.map(d => (
                <button
                  key={d.id}
                  onClick={() => sendOpen(d.id)}
                  disabled={sending}
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
            <button onClick={() => setShowPicker(false)} className="w-full mt-4 py-2 text-xs text-zinc-500 hover:text-zinc-300" data-testid="turnstile-picker-close">
              Cancelar
            </button>
          </div>
        </div>
      )}
    </>
  );
}
