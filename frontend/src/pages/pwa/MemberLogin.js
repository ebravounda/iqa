import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Loader2, QrCode } from 'lucide-react';
import { toast } from 'sonner';

export default function MemberLogin() {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginMember } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!code || code.length < 6) {
      toast.error('Ingresa tu código de socio (6 caracteres)');
      return;
    }

    setLoading(true);
    try {
      await loginMember(code.toUpperCase());
      toast.success('¡Bienvenido!');
      navigate('/app');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Código no encontrado');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (e) => {
    const value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    setCode(value);
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-6 noise-overlay">
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-10"
        style={{ backgroundImage: 'url(https://images.pexels.com/photos/6388373/pexels-photo-6388373.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
      />
      
      <div className="relative z-10 w-full max-w-sm">
        <div className="text-center mb-10">
          <div 
            className="w-20 h-20 rounded-2xl mx-auto mb-6 flex items-center justify-center"
            style={{ backgroundColor: 'var(--gym-primary)' }}
          >
            <QrCode size={40} className="text-black" />
          </div>
          <h1 className="text-3xl font-black tracking-tight mb-2">GymAccess</h1>
          <p className="text-zinc-400">Ingresa con tu código de socio</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-3 text-center">
              Código de Socio
            </label>
            <Input
              type="text"
              value={code}
              onChange={handleCodeChange}
              placeholder="SD345FG"
              className="input-dark text-center text-2xl font-mono tracking-[0.3em] h-16"
              maxLength={6}
              autoComplete="off"
              data-testid="member-code-input"
            />
            <p className="text-center text-xs text-zinc-500 mt-2">
              Tu código está en tu tarjeta de socio o email de bienvenida
            </p>
          </div>

          <Button
            type="submit"
            disabled={loading || code.length < 6}
            className="w-full btn-gym-primary h-14 text-lg"
            data-testid="member-login-btn"
          >
            {loading ? (
              <Loader2 className="animate-spin mr-2" size={24} />
            ) : (
              <QrCode className="mr-2" size={24} />
            )}
            Ingresar
          </Button>
        </form>

        <p className="text-center text-xs text-zinc-600 mt-8">
          ¿No tienes cuenta? Consulta en recepción
        </p>
      </div>
    </div>
  );
}
