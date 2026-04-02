import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { UserPlus, CheckCircle, CreditCard, QrCode, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PublicRegister() {
  const { gymId } = useParams();
  const navigate = useNavigate();
  const [gym, setGym] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    plan_id: '',
    gender: 'prefer_not_to_say'
  });
  const [customForms, setCustomForms] = useState([]);
  const [formResponses, setFormResponses] = useState({});

  useEffect(() => {
    fetchGymInfo();
  }, [gymId]);

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
      // Fetch custom forms
      try {
        const formsRes = await axios.get(`${API}/forms/public/${gymId}`);
        setCustomForms(formsRes.data);
      } catch (e) {}
    } catch (error) {
      toast.error('Gimnasio no encontrado');
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
      const payload = {
        name: formData.name,
        email: formData.email,
        phone: formData.phone || null,
        gym_id: gymId,
        plan_id: formData.plan_id || null,
        gender: formData.gender || 'prefer_not_to_say',
        form_responses: Object.keys(formResponses).length > 0 ? formResponses : null
      };
      const response = await axios.post(`${API}/members/register`, payload);
      setSuccess(response.data);

      // Submit custom form responses
      if (customForms.length > 0 && Object.keys(formResponses).length > 0 && response.data.member?.id) {
        for (const form of customForms) {
          try {
            await axios.post(`${API}/forms/${form.id}/responses`, {
              member_id: response.data.member.id,
              responses: formResponses
            });
          } catch (e) {}
        }
      }

      // Auto-login the member (token needed for payment)
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('userType', 'member');
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrarse');
    } finally {
      setSubmitting(false);
    }
  };

  const goToApp = () => {
    window.location.href = '/app';
  };

  const goToPayment = async () => {
    if (!success?.plan?.id) return;
    try {
      const res = await axios.post(`${API}/payments/checkout?plan_id=${success.plan.id}`);
      if (res.data.url) {
        window.location.href = res.data.url;
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al iniciar pago. Contacta al administrador.');
    }
  };

  const selectedPlan = plans.find(p => p.id === formData.plan_id);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!gym) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-red-500 mb-2">Gimnasio no encontrado</p>
          <p className="text-zinc-400">El enlace de registro no es válido.</p>
        </div>
      </div>
    );
  }

  if (success) {
    const requiresPayment = success.requires_payment && success.plan;
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <div className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center" style={{ backgroundColor: requiresPayment ? '#F59E0B' : 'var(--gym-primary)', color: '#000' }}>
            {requiresPayment ? <CreditCard size={40} /> : <CheckCircle size={40} />}
          </div>
          <h1 className="text-3xl font-black mb-2">{requiresPayment ? 'Registro Exitoso' : 'Registro Exitoso'}</h1>
          <p className="text-zinc-400 mb-6">Ya eres miembro de <strong className="text-white">{gym.name}</strong></p>

          <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl p-6 mb-6" data-testid="registration-success">
            <div className="flex items-center justify-center gap-3 mb-4">
              <QrCode size={24} style={{ color: 'var(--gym-primary)' }} />
              <span className="text-lg font-bold">Tu codigo de acceso</span>
            </div>
            <p className="text-4xl font-black font-mono tracking-widest mb-2" style={{ color: 'var(--gym-primary)' }} data-testid="member-code">
              {success.member.code}
            </p>
            <p className="text-xs text-zinc-500">Guarda este codigo para acceder al gimnasio</p>
          </div>

          {requiresPayment && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 mb-6" data-testid="payment-required-box">
              <CreditCard size={24} className="mx-auto mb-3 text-amber-400" />
              <p className="text-amber-300 font-bold text-lg mb-2">Pago pendiente</p>
              <p className="text-zinc-400 text-sm mb-1">
                Para habilitar tu acceso al gimnasio, realiza el pago de tu membresia:
              </p>
              <p className="text-white font-bold text-xl mb-1">{success.plan.name}</p>
              <p className="text-2xl font-black" style={{ color: 'var(--gym-primary)' }}>
                {success.plan.price?.toFixed(2)} {(success.plan.currency || gym.currency || 'EUR').toUpperCase()}
              </p>
              <p className="text-zinc-500 text-xs mt-1">{success.plan.duration_days} dias de acceso</p>
            </div>
          )}

          {requiresPayment ? (
            <Button onClick={goToPayment} className="w-full text-lg py-3 bg-amber-500 hover:bg-amber-600 text-black font-bold" data-testid="pay-now-btn">
              <CreditCard size={20} className="mr-2" />
              Pagar Ahora
            </Button>
          ) : (
            <Button onClick={goToApp} className="w-full btn-gym-primary text-lg py-3" data-testid="go-to-app-btn">
              <QrCode size={20} className="mr-2" />
              Ir a Mi QR de Acceso
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Gym Header */}
        <div className="text-center mb-8">
          {gym.logo_url ? (
            <img src={gym.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${gym.logo_url}` : gym.logo_url} alt={gym.name} className="w-20 h-20 rounded-2xl mx-auto mb-4 object-cover" />
          ) : (
            <div
              className="w-20 h-20 rounded-2xl mx-auto mb-4 flex items-center justify-center font-black text-3xl"
              style={{ backgroundColor: 'var(--gym-primary)', color: '#000' }}
            >
              {gym.name?.charAt(0)}
            </div>
          )}
          <h1 className="text-3xl font-black tracking-tight mb-1">{gym.name}</h1>
          <p className="text-zinc-400">Regístrate como socio</p>
          {gym.address && <p className="text-zinc-500 text-sm mt-1">{gym.address}</p>}
        </div>

        {/* Registration Form */}
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Nombre completo</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Tu nombre completo"
                className="input-dark"
                data-testid="register-name-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Email</label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="tu@email.com"
                className="input-dark"
                data-testid="register-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Telefono (opcional)</label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+34 600 000 000"
                className="input-dark"
                data-testid="register-phone-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Sexo</label>
              <select className="input-gym w-full" value={formData.gender} onChange={e => setFormData({ ...formData, gender: e.target.value })} data-testid="register-gender-select">
                <option value="male">Hombre</option>
                <option value="female">Mujer</option>
                <option value="prefer_not_to_say">Prefiero no contestar</option>
              </select>
            </div>

            {customForms.length > 0 && customForms.map(form => (
              <div key={form.id} className="border border-zinc-700 rounded-xl p-4 space-y-3" data-testid={`custom-form-${form.id}`}>
                <h4 className="text-sm font-semibold text-white">{form.name}</h4>
                {form.description && <p className="text-xs text-zinc-400">{form.description}</p>}
                {(form.fields || []).map((field, idx) => (
                  <div key={idx}>
                    <label className="text-xs text-zinc-400 block mb-1">{field.label}{field.required && ' *'}</label>
                    {field.field_type === 'text' && (
                      <input className="input-gym text-sm" placeholder={field.placeholder || ''} value={formResponses[field.label] || ''} onChange={e => setFormResponses({ ...formResponses, [field.label]: e.target.value })} required={field.required} />
                    )}
                    {field.field_type === 'textarea' && (
                      <textarea className="input-gym text-sm" placeholder={field.placeholder || ''} rows={2} value={formResponses[field.label] || ''} onChange={e => setFormResponses({ ...formResponses, [field.label]: e.target.value })} required={field.required} />
                    )}
                    {field.field_type === 'select' && (
                      <select className="input-gym text-sm" value={formResponses[field.label] || ''} onChange={e => setFormResponses({ ...formResponses, [field.label]: e.target.value })} required={field.required}>
                        <option value="">Seleccionar...</option>
                        {(field.options || []).map((opt, i) => <option key={i} value={opt}>{opt}</option>)}
                      </select>
                    )}
                    {field.field_type === 'checkbox' && (
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={formResponses[field.label] === 'Si'} onChange={e => setFormResponses({ ...formResponses, [field.label]: e.target.checked ? 'Si' : 'No' })} className="accent-[var(--gym-primary)]" />
                        <span className="text-sm text-zinc-300">Si</span>
                      </label>
                    )}
                    {field.field_type === 'number' && (
                      <input type="number" className="input-gym text-sm" placeholder={field.placeholder || ''} value={formResponses[field.label] || ''} onChange={e => setFormResponses({ ...formResponses, [field.label]: e.target.value })} required={field.required} />
                    )}
                  </div>
                ))}
              </div>
            ))}

            {plans.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Selecciona un plan (opcional)</label>
                <div className="space-y-3">
                  {plans.map((plan) => (
                    <button
                      key={plan.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, plan_id: formData.plan_id === plan.id ? '' : plan.id })}
                      className={`w-full text-left p-4 rounded-xl border transition-all ${
                        formData.plan_id === plan.id
                          ? 'border-[var(--gym-primary)] bg-[var(--gym-primary)]/5'
                          : 'border-zinc-700 hover:border-zinc-600'
                      }`}
                      data-testid={`plan-option-${plan.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-bold">{plan.name}</p>
                          {plan.description && <p className="text-xs text-zinc-500 mt-0.5">{plan.description}</p>}
                          <p className="text-xs text-zinc-500 mt-1">{plan.duration_days} días</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-black" style={{ color: formData.plan_id === plan.id ? 'var(--gym-primary)' : 'white' }}>
                            {gym.currency === 'eur' ? '€' : '$'}{plan.price}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <Button
              type="submit"
              disabled={submitting}
              className="w-full btn-gym-primary text-lg py-3"
              data-testid="register-submit-btn"
            >
              {submitting ? (
                <Loader2 className="animate-spin mr-2" size={20} />
              ) : (
                <UserPlus className="mr-2" size={20} />
              )}
              Registrarme
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-xs text-zinc-500">
              ¿Ya tienes cuenta?{' '}
              <a href="/app/login" className="text-[var(--gym-primary)] hover:underline">Iniciar sesión</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
