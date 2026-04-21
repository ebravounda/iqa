import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Loader2, ShieldCheck, AlertOctagon, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export default function MemberLogin() {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [focused, setFocused] = useState(0);
  const { loginMember, gym } = useAuth();
  const navigate = useNavigate();
  const inputRefs = useRef([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const fullCode = code.join('');
    if (fullCode.length < 6) {
      toast.error('Ingresa tu codigo de socio (6 caracteres)');
      return;
    }

    setLoading(true);
    try {
      await loginMember(fullCode.toUpperCase());
      toast.success('Bienvenido!');
      navigate('/app');
    } catch (error) {
      const detail = error.response?.data?.detail || '';
      if (detail === 'Cuenta Bloqueada') {
        setBlocked(true);
      } else {
        toast.error(detail || 'Codigo no encontrado');
        setCode(['', '', '', '', '', '']);
        setTimeout(() => inputRefs.current[0]?.focus(), 100);
      }
    } finally {
      setLoading(false);
    }
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

    // Auto-submit when all 6 filled
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
        <form onSubmit={handleSubmit} className="space-y-8">
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
        <div className="mt-10 text-center">
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
