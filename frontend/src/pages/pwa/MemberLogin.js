import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Loader2, ShieldCheck, AlertOctagon, ArrowRight, Smartphone, Trash2, Monitor, Tablet, Mail } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function DeviceIcon({ name }) {
  const n = (name || '').toLowerCase();
  if (n.includes('iphone') || n.includes('samsung') || n.includes('android') || n.includes('huawei') || n.includes('xiaomi'))
    return <Smartphone size={18} />;
  if (n.includes('ipad') || n.includes('tablet'))
    return <Tablet size={18} />;
  return <Monitor size={18} />;
}

export default function MemberLogin() {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [focused, setFocused] = useState(0);
  const [rememberMe, setRememberMe] = useState(false);
  const [autoLogging, setAutoLogging] = useState(false);
  const [recoveryMode, setRecoveryMode] = useState(false);
  const [recoveryEmail, setRecoveryEmail] = useState('');
  const [recoverySent, setRecoverySent] = useState(false);
  const [recoveryLoading, setRecoveryLoading] = useState(false);  const [deviceLimitHit, setDeviceLimitHit] = useState(false);
  const [devices, setDevices] = useState([]);
  const [maxDevices, setMaxDevices] = useState(2);
  const [deactivating, setDeactivating] = useState(null);
  const [savedCode, setSavedCode] = useState(''); // Store code for device deactivation

  // Device limit state
  const { loginMember, gym } = useAuth();
  const navigate = useNavigate();
  const inputRefs = useRef([]);

  // Auto-login with remembered code
  useEffect(() => {
    const saved = localStorage.getItem('remembered_code');
    if (saved && saved.length === 6) {
      setAutoLogging(true);
      setRememberMe(true);
      doLogin(saved);
    } else {
      inputRefs.current[0]?.focus();
    }
  }, []);

  const doLogin = async (fullCode) => {
    setLoading(true);
    try {
      await loginMember(fullCode.toUpperCase());
      // Save code if remember me is on
      if (rememberMe || localStorage.getItem('remembered_code')) {
        localStorage.setItem('remembered_code', fullCode.toUpperCase());
      }
      toast.success('Bienvenido!');
      navigate('/app');
    } catch (error) {
      const detail = error.response?.data?.detail || '';
      if (detail === 'Cuenta Bloqueada') {
        setBlocked(true);
      } else if (detail.startsWith('DEVICE_LIMIT|')) {
        // Device limit exceeded - show device manager
        const msg = detail.replace('DEVICE_LIMIT|', '');
        toast.error(msg);
        setSavedCode(fullCode.toUpperCase()); // Save code for deactivation
        await fetchDevices(fullCode.toUpperCase());
      } else {
        toast.error(detail || 'Codigo no encontrado');
        localStorage.removeItem('remembered_code');
        setCode(['', '', '', '', '', '']);
        setTimeout(() => inputRefs.current[0]?.focus(), 100);
      }
      setAutoLogging(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchDevices = async (memberCode) => {
    try {
      const res = await axios.get(`${API}/my-devices-by-code?code=${memberCode}`);
      setDevices(res.data.devices);
      setMaxDevices(res.data.max_devices);
      setDeviceLimitHit(true);
    } catch {
      toast.error('Error al cargar dispositivos');
    }
  };

  const handleDeactivateDevice = async (deviceId) => {
    const fullCode = savedCode || code.join('');
    if (!fullCode) {
      toast.error('Error: codigo no disponible');
      return;
    }
    setDeactivating(deviceId);
    try {
      await axios.put(`${API}/my-devices-by-code/${deviceId}/deactivate?code=${fullCode}`);
      setDevices(prev => prev.filter(d => d.id !== deviceId));
      toast.success('Dispositivo desactivado');
      // If now under limit, retry login
      if (devices.length - 1 < maxDevices) {
        setDeviceLimitHit(false);
        toast.info('Intentando ingresar de nuevo...');
        setTimeout(() => doLogin(fullCode), 500);
      }
    } catch {
      toast.error('Error al desactivar dispositivo');
    } finally {
      setDeactivating(null);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const fullCode = code.join('');
    if (fullCode.length < 6) {
      toast.error('Ingresa tu codigo de socio (6 caracteres)');
      return;
    }
    // Save remember preference
    if (rememberMe) {
      localStorage.setItem('remembered_code', fullCode.toUpperCase());
    } else {
      localStorage.removeItem('remembered_code');
    }
    await doLogin(fullCode);
  };

  const handleChange = (index, value) => {
    const char = value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(-1);
    const newCode = [...code];
    newCode[index] = char;
    setCode(newCode);

    if (char && index < 5) {
      inputRefs.current[index + 1]?.focus();
      setFocused(index + 1);
    }

    if (char && index === 5 && newCode.every(c => c)) {
      setTimeout(() => {
        const fullCode = newCode.join('');
        if (fullCode.length === 6) handleSubmit();
      }, 150);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
      setFocused(index - 1);
      const newCode = [...code];
      newCode[index - 1] = '';
      setCode(newCode);
    }
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    if (pasted.length > 0) {
      const newCode = [...code];
      for (let i = 0; i < pasted.length && i < 6; i++) {
        newCode[i] = pasted[i];
      }
      setCode(newCode);
      const nextFocus = Math.min(pasted.length, 5);
      inputRefs.current[nextFocus]?.focus();
      setFocused(nextFocus);

      if (pasted.length === 6) {
        setTimeout(() => handleSubmit(), 150);
      }
    }
  };

  const fullCode = code.join('');
  const isComplete = fullCode.length === 6;

  const handleRecoverCode = async (e) => {
    if (e) e.preventDefault();
    if (!recoveryEmail.trim()) { toast.error('Ingresa tu email'); return; }
    setRecoveryLoading(true);
    try {
      await axios.post(`${API}/auth/member/recover-code`, { email: recoveryEmail.trim() });
      setRecoverySent(true);
      toast.success('Si tu email esta registrado, recibiras tu codigo');
    } catch {
      toast.error('Error al enviar. Intenta de nuevo.');
    } finally {
      setRecoveryLoading(false);
    }
  };

  // Auto-login loading screen
  if (autoLogging) {
    return (
      <div className="min-h-screen bg-[#09090B] flex flex-col items-center justify-center p-6" data-testid="auto-login-screen">
        <Loader2 className="animate-spin mb-4" size={40} style={{ color: 'var(--gym-primary)' }} />
        <p className="text-zinc-400 text-sm">Iniciando sesion...</p>
      </div>
    );
  }

  // Blocked screen
  if (blocked) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-6" data-testid="member-blocked-screen">
        <div className="w-full max-w-sm text-center space-y-6">
          <div className="w-20 h-20 rounded-full bg-red-500/10 border-2 border-red-500/30 flex items-center justify-center mx-auto">
            <AlertOctagon size={40} className="text-red-500" />
          </div>
          <div>
            <h1 className="text-2xl font-black mb-2">Cuenta Bloqueada</h1>
            <p className="text-zinc-400 text-sm leading-relaxed">
              El acceso a tu gimnasio ha sido temporalmente suspendido.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
            <p className="text-zinc-400 text-sm">Comunicate con la administracion de tu gimnasio para mas informacion.</p>
          </div>
          <button 
            onClick={() => { setBlocked(false); setCode(['', '', '', '', '', '']); }}
            className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
            data-testid="back-to-login-btn"
          >
            Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  // Device limit screen
  if (deviceLimitHit) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-6" data-testid="device-limit-screen">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-amber-500/10 border-2 border-amber-500/30 flex items-center justify-center mx-auto mb-4">
              <Smartphone size={32} className="text-amber-500" />
            </div>
            <h1 className="text-xl font-black mb-2">Limite de dispositivos</h1>
            <p className="text-zinc-400 text-sm">
              Ya tienes {devices.length} dispositivo{devices.length !== 1 ? 's' : ''} registrado{devices.length !== 1 ? 's' : ''} (maximo {maxDevices}).
              Desactiva uno para poder acceder desde este.
            </p>
          </div>

          <div className="space-y-3">
            {devices.map(device => (
              <div 
                key={device.id} 
                className="flex items-center justify-between p-4 rounded-xl bg-zinc-900/80 border border-zinc-800"
                data-testid={`device-item-${device.id}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-400">
                    <DeviceIcon name={device.device_name} />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{device.device_name || 'Dispositivo'}</p>
                    <p className="text-xs text-zinc-500">
                      {device.last_active ? new Date(device.last_active).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' }) : ''}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeactivateDevice(device.id)}
                  disabled={deactivating === device.id}
                  className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  data-testid={`deactivate-device-${device.id}`}
                >
                  {deactivating === device.id ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Trash2 size={16} />
                  )}
                </Button>
              </div>
            ))}
          </div>

          <button 
            onClick={() => { setDeviceLimitHit(false); setCode(['', '', '', '', '', '']); }}
            className="w-full text-sm text-zinc-500 hover:text-zinc-300 transition-colors text-center py-2"
            data-testid="back-from-devices-btn"
          >
            Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  // Recovery screen
  if (recoveryMode) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-6" data-testid="recovery-screen">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center mx-auto mb-4">
              <Mail size={32} className="text-blue-500" />
            </div>
            <h1 className="text-xl font-black mb-2">{recoverySent ? 'Email enviado' : 'Recuperar codigo'}</h1>
            <p className="text-zinc-400 text-sm">
              {recoverySent 
                ? 'Si tu email esta registrado, recibiras tu codigo de socio en breve. Revisa tu bandeja de entrada y spam.'
                : 'Ingresa tu email y te enviaremos tu codigo de socio.'
              }
            </p>
          </div>

          {!recoverySent && (
            <form onSubmit={handleRecoverCode} className="space-y-4">
              <input
                type="email"
                value={recoveryEmail}
                onChange={(e) => setRecoveryEmail(e.target.value)}
                placeholder="tu@email.com"
                className="w-full h-14 px-4 bg-zinc-900/80 border-2 border-zinc-800 rounded-xl text-white outline-none focus:border-[var(--gym-primary)] transition-colors"
                autoFocus
                data-testid="recovery-email-input"
              />
              <Button
                type="submit"
                disabled={recoveryLoading || !recoveryEmail.trim()}
                className="w-full h-14 text-base font-bold rounded-xl"
                style={recoveryEmail.trim() ? { backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' } : {}}
                data-testid="recovery-submit-btn"
              >
                {recoveryLoading ? <Loader2 className="animate-spin" size={22} /> : 'Enviar codigo'}
              </Button>
            </form>
          )}

          <button
            onClick={() => { setRecoveryMode(false); setRecoverySent(false); setRecoveryEmail(''); }}
            className="w-full text-sm text-zinc-500 hover:text-zinc-300 transition-colors text-center py-2"
            data-testid="back-from-recovery-btn"
          >
            Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090B] flex flex-col items-center justify-center p-6 relative overflow-hidden" data-testid="member-login-screen">
      {/* Ambient glow */}
      <div 
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full blur-[120px] opacity-[0.07]"
        style={{ backgroundColor: 'var(--gym-primary)' }}
      />
      <div 
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[400px] h-[200px] rounded-full blur-[100px] opacity-[0.04]"
        style={{ backgroundColor: 'var(--gym-primary)' }}
      />

      <div className="relative z-10 w-full max-w-sm">
        {/* Logo / Branding */}
        <div className="text-center mb-12">
          {gym?.logo_url ? (
            <img 
              src={gym.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${gym.logo_url}` : gym.logo_url} 
              alt={gym?.name} 
              className="h-16 max-w-[180px] mx-auto mb-6 object-contain"
              data-testid="gym-logo"
            />
          ) : (
            <div className="mb-6 flex items-center justify-center">
              <div 
                className="w-16 h-16 rounded-2xl flex items-center justify-center font-black text-2xl shadow-lg"
                style={{ 
                  backgroundColor: 'var(--gym-primary)', 
                  color: 'var(--gym-primary-foreground)',
                  boxShadow: '0 0 40px rgba(225, 255, 1, 0.15)'
                }}
              >
                {gym?.name?.charAt(0) || 'Q'}
              </div>
            </div>
          )}
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight mb-2">
            {gym?.name || 'IngresoQR'}
          </h1>
          <p className="text-zinc-500 text-sm">
            Ingresa tu codigo de socio para acceder
          </p>
        </div>

        {/* Code Input */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <div className="flex gap-2 sm:gap-3 justify-center" data-testid="code-input-group">
              {code.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => (inputRefs.current[index] = el)}
                  type="text"
                  inputMode="text"
                  autoCapitalize="characters"
                  autoComplete="off"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onFocus={() => setFocused(index)}
                  onPaste={index === 0 ? handlePaste : undefined}
                  className={`
                    w-12 h-14 sm:w-14 sm:h-16 text-center text-xl sm:text-2xl font-mono font-bold
                    rounded-xl border-2 bg-zinc-900/80 outline-none
                    transition-all duration-200
                    ${digit ? 'border-zinc-600 text-white' : 'border-zinc-800 text-zinc-400'}
                    ${focused === index ? 'border-[var(--gym-primary)] shadow-[0_0_20px_rgba(225,255,1,0.1)]' : ''}
                  `}
                  style={focused === index ? { borderColor: 'var(--gym-primary)' } : {}}
                  data-testid={`member-code-input-${index}`}
                />
              ))}
            </div>
            <p className="text-center text-xs text-zinc-600 mt-4">
              Tu codigo esta en tu tarjeta de socio o email de bienvenida
            </p>
          </div>

          {/* Remember Me */}
          <label 
            className="flex items-center justify-center gap-3 cursor-pointer select-none group"
            data-testid="remember-me-label"
          >
            <div className="relative">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => {
                  setRememberMe(e.target.checked);
                  if (!e.target.checked) localStorage.removeItem('remembered_code');
                }}
                className="sr-only peer"
                data-testid="remember-me-checkbox"
              />
              <div className="w-9 h-5 bg-zinc-800 rounded-full peer-checked:bg-[var(--gym-primary)] transition-colors" />
              <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-zinc-400 rounded-full transition-all peer-checked:translate-x-4 peer-checked:bg-black" />
            </div>
            <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">Recordarme</span>
          </label>

          <Button
            type="submit"
            disabled={loading || !isComplete}
            className="w-full h-14 text-base font-bold rounded-xl transition-all duration-300"
            style={isComplete ? { 
              backgroundColor: 'var(--gym-primary)', 
              color: 'var(--gym-primary-foreground)',
              boxShadow: '0 0 30px rgba(225, 255, 1, 0.15)'
            } : {}}
            data-testid="member-login-btn"
          >
            {loading ? (
              <Loader2 className="animate-spin mr-2" size={22} />
            ) : (
              <div className="flex items-center justify-center gap-2">
                <ShieldCheck size={20} />
                <span>Acceder</span>
                <ArrowRight size={18} className={`transition-transform duration-300 ${isComplete ? 'translate-x-0 opacity-100' : '-translate-x-2 opacity-0'}`} />
              </div>
            )}
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-8 text-center space-y-3">
          <button
            onClick={() => setRecoveryMode(true)}
            className="text-sm text-zinc-400 hover:text-white transition-colors"
            data-testid="forgot-code-btn"
          >
            Olvide mi codigo
          </button>
          <p className="text-xs text-zinc-700">
            No tienes cuenta? Consulta en recepcion
          </p>
        </div>

        {/* Security badge */}
        <div className="mt-6 flex items-center justify-center gap-1.5 text-zinc-700">
          <ShieldCheck size={12} />
          <span className="text-[10px] tracking-wider uppercase">Acceso seguro</span>
        </div>
      </div>
    </div>
  );
}
