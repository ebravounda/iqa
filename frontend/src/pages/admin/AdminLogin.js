import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useCustomDomain } from '../../hooks/useCustomDomain';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Loader2, LogIn } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginAdmin } = useAuth();
  const navigate = useNavigate();
  const { domainGym, isCustomDomain, loading: domainLoading } = useCustomDomain();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Por favor ingresa email y contraseña');
      return;
    }

    setLoading(true);
    try {
      await loginAdmin(email, password);
      toast.success('Bienvenido!');
      navigate('/admin');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Credenciales invalidas');
    } finally {
      setLoading(false);
    }
  };

  if (domainLoading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <Loader2 className="animate-spin text-zinc-500" size={32} />
      </div>
    );
  }

  const gymColor = domainGym?.primary_color || 'var(--gym-primary)';
  const gymName = domainGym?.name;
  const gymLogo = domainGym?.logo_url;
  const API = process.env.REACT_APP_BACKEND_URL;

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4 noise-overlay">
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-10"
        style={{ backgroundImage: 'url(https://images.pexels.com/photos/6388373/pexels-photo-6388373.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
      />
      
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          {gymLogo ? (
            <img 
              src={gymLogo.startsWith('/') ? `${API}${gymLogo}` : gymLogo} 
              alt={gymName} 
              className="w-20 h-20 object-contain mx-auto mb-4 rounded-xl"
            />
          ) : null}
          <h1 className="text-4xl font-black tracking-tight mb-2">
            {gymName ? (
              <span style={{ color: gymColor }}>{gymName}</span>
            ) : (
              <><span style={{ color: gymColor }}>Ingreso</span>QR</>
            )}
          </h1>
          <p className="text-zinc-400">
            {isCustomDomain && domainGym ? 'Panel de Administracion' : 'Panel de Administracion'}
          </p>
        </div>

        <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl p-8"
          style={domainGym ? { borderColor: `${gymColor}22` } : {}}>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@tunegocio.com"
                className="input-dark"
                data-testid="admin-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">
                Contrasena
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input-dark"
                data-testid="admin-password-input"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full"
              style={{ background: gymColor, color: '#000' }}
              data-testid="admin-login-btn"
            >
              {loading ? (
                <Loader2 className="animate-spin mr-2" size={20} />
              ) : (
                <LogIn className="mr-2" size={20} />
              )}
              Iniciar Sesion
            </Button>
          </form>

          {isCustomDomain && !domainGym && (
            <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <p className="text-red-400 text-sm text-center">Dominio no configurado</p>
            </div>
          )}

          <p className="text-center text-xs text-zinc-500 mt-6">
            {gymName ? `Acceso exclusivo para personal de ${gymName}` : 'Inicia sesion con tus credenciales de acceso'}
          </p>
        </div>
      </div>
    </div>
  );
}
