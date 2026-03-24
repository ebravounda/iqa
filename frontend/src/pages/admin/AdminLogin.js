import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
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
      toast.error(error.response?.data?.detail || 'Credenciales inválidas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4 noise-overlay">
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-10"
        style={{ backgroundImage: 'url(https://images.pexels.com/photos/6388373/pexels-photo-6388373.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
      />
      
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-black tracking-tight mb-2">
            <span style={{ color: 'var(--gym-primary)' }}>GYM</span>ACCESS
          </h1>
          <p className="text-zinc-400">Panel de Administración</p>
        </div>

        <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@gymaccess.com"
                className="input-dark"
                data-testid="admin-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">
                Contraseña
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
              className="w-full btn-gym-primary"
              data-testid="admin-login-btn"
            >
              {loading ? (
                <Loader2 className="animate-spin mr-2" size={20} />
              ) : (
                <LogIn className="mr-2" size={20} />
              )}
              Iniciar Sesión
            </Button>
          </form>

          <p className="text-center text-xs text-zinc-500 mt-6">
            Credenciales por defecto: admin@gymaccess.com / admin123
          </p>
        </div>
      </div>
    </div>
  );
}
