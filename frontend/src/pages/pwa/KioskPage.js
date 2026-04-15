import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';
import { UserPlus, CheckCircle, QrCode, Loader2, RotateCcw, Mail } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function KioskPage() {
  const { gymId } = useParams();
  const [gym, setGym] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    plan_id: ''
  });

  useEffect(() => { fetchGymInfo(); }, [gymId]);

  // Auto-reset after 30 seconds on success screen
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => resetForm(), 30000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const fetchGymInfo = async () => {
    try {
      const [gymRes, plansRes] = await Promise.all([
        axios.get(`${API}/gyms/${gymId}/public-info`),
        axios.get(`${API}/plans/public/${gymId}`)
      ]);
      setGym(gymRes.data);
      setPlans(plansRes.data);
      if (gymRes.data.primary_color) {
        document.documentElement.style.setProperty('--gym-primary', gymRes.data.primary_color);
      }
    } catch (error) {
      toast.error('Kiosko no disponible');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.email) {
      toast.error('Nombre y email son requeridos');
      return;
    }
    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/kiosk/register`, {
        name: formData.name,
        email: formData.email,
        phone: formData.phone || null,
        gym_id: gymId,
        plan_id: formData.plan_id || null
      });
      setSuccess(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrarse');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setSuccess(null);
    setFormData({ name: '', email: '', phone: '', plan_id: '' });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-12 h-12 border-3 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!gym) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <p className="text-2xl font-bold text-red-500">Kiosko no disponible</p>
      </div>
    );
  }

  // Success Screen - shows for 30 seconds then resets
  if (success) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-6">
        <div className="w-full max-w-lg text-center">
          <div className="w-28 h-28 rounded-full mx-auto mb-8 flex items-center justify-center" style={{ backgroundColor: 'var(--gym-primary)', color: '#000' }}>
            <CheckCircle size={56} />
          </div>
          
          <h1 className="text-4xl font-black mb-2">Registro Exitoso</h1>
          <p className="text-zinc-400 text-xl mb-8">Bienvenido/a a <strong className="text-white">{gym.name}</strong></p>

          <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-3xl p-8 mb-8" data-testid="kiosk-success">
            <div className="flex items-center justify-center gap-3 mb-6">
              <QrCode size={28} style={{ color: 'var(--gym-primary)' }} />
              <span className="text-xl font-bold">Tu código de acceso</span>
            </div>
            <p className="text-6xl font-black font-mono tracking-[0.3em] mb-4" style={{ color: 'var(--gym-primary)' }} data-testid="kiosk-member-code">
              {success.member.code}
            </p>
            
            {success.email_sent && (
              <div className="flex items-center justify-center gap-2 mt-4 text-emerald-400">
                <Mail size={18} />
                <span className="text-sm">Email enviado a {success.member.email}</span>
              </div>
            )}
            
            <p className="text-zinc-500 text-sm mt-4">
              Revisa tu email para completar el pago de tu membresía
            </p>
          </div>

          <Button onClick={resetForm} variant="outline" className="border-zinc-700 text-lg px-8 py-3" data-testid="kiosk-new-register">
            <RotateCcw size={20} className="mr-2" />
            Nuevo Registro
          </Button>
          
          <p className="text-zinc-600 text-xs mt-6">Esta pantalla se reiniciará automáticamente en 30 segundos</p>
        </div>
      </div>
    );
  }

  // Registration Form - Kiosk optimized (large fonts, touch-friendly)
  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        {/* Gym Header */}
        <div className="text-center mb-10">
          {gym.logo_url ? (
            <img src={gym.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${gym.logo_url}` : gym.logo_url} alt={gym.name} className="h-24 max-w-[200px] mx-auto mb-4 object-contain" />
          ) : (
            <div className="w-24 h-24 rounded-3xl mx-auto mb-4 flex items-center justify-center font-black text-4xl"
              style={{ backgroundColor: 'var(--gym-primary)', color: '#000' }}>
              {gym.name?.charAt(0)}
            </div>
          )}
          <h1 className="text-4xl font-black tracking-tight">{gym.name}</h1>
          <p className="text-zinc-400 text-xl mt-1">Regístrate aquí</p>
        </div>

        {/* Form */}
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-3xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-base font-medium text-zinc-300 mb-2">Nombre completo</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Tu nombre completo"
                className="input-dark text-lg py-4"
                data-testid="kiosk-name-input"
              />
            </div>

            <div>
              <label className="block text-base font-medium text-zinc-300 mb-2">Email</label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="tu@email.com"
                className="input-dark text-lg py-4"
                data-testid="kiosk-email-input"
              />
            </div>

            <div>
              <label className="block text-base font-medium text-zinc-300 mb-2">Teléfono</label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+34 600 000 000"
                className="input-dark text-lg py-4"
                data-testid="kiosk-phone-input"
              />
            </div>

            {plans.length > 0 && (
              <div>
                <label className="block text-base font-medium text-zinc-300 mb-3">Selecciona tu plan</label>
                <div className="space-y-3">
                  {plans.map((plan) => (
                    <button
                      key={plan.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, plan_id: formData.plan_id === plan.id ? '' : plan.id })}
                      className={`w-full text-left p-5 rounded-2xl border-2 transition-all ${
                        formData.plan_id === plan.id
                          ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/5'
                          : 'border-zinc-700 hover:border-zinc-500'
                      }`}
                      data-testid={`kiosk-plan-${plan.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-bold text-lg">{plan.name}</p>
                          <p className="text-sm text-zinc-500">{plan.duration_days} días</p>
                        </div>
                        <p className="text-2xl font-black" style={{ color: formData.plan_id === plan.id ? 'var(--gym-primary)' : 'white' }}>
                          ${plan.price}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <Button
              type="submit"
              disabled={submitting}
              className="w-full btn-gym-primary text-xl py-5 mt-4"
              data-testid="kiosk-submit-btn"
            >
              {submitting ? (
                <Loader2 className="animate-spin mr-2" size={24} />
              ) : (
                <UserPlus className="mr-2" size={24} />
              )}
              Registrarme
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
