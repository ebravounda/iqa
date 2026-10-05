import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getPlansPublic, createCheckout, getPaymentStatus, initiateRedsysPayment, getRedsysPaymentStatus } from '../../lib/api';
import { formatCurrency, formatDate, getDaysRemaining, getMembershipStatus } from '../../lib/utils';
import { Button } from '../../components/ui/button';
import { motion } from 'framer-motion';
import { CreditCard, Calendar, Clock, Check, AlertTriangle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

export default function MemberMembership() {
  const { member, gym, membership, plan, refreshMemberData } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [redsysPayUrl, setRedsysPayUrl] = useState(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const membershipStatus = getMembershipStatus(membership);
  const daysRemaining = membership ? getDaysRemaining(membership.end_date) : 0;

  useEffect(() => {
    fetchPlans();
    
    // Check for Stripe payment success
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      checkPaymentStatus(sessionId);
    }

    // Check for Redsys payment result
    const redsysResult = searchParams.get('redsys_result');
    const redsysOrder = searchParams.get('order');
    if (redsysResult && redsysOrder) {
      checkRedsysResult(redsysResult, redsysOrder);
    }
  }, [searchParams]);

  const fetchPlans = async () => {
    if (!gym?.id) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await getPlansPublic(gym.id);
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async (sessionId) => {
    setProcessingPayment(true);
    let attempts = 0;
    const maxAttempts = 10;

    const poll = async () => {
      try {
        const response = await getPaymentStatus(sessionId);
        
        if (response.data.payment_status === 'paid') {
          toast.success('¡Pago exitoso! Tu membresía ha sido activada');
          await refreshMemberData();
          navigate('/app/membership', { replace: true });
          setProcessingPayment(false);
          return;
        } else if (response.data.status === 'expired') {
          toast.error('La sesión de pago ha expirado');
          setProcessingPayment(false);
          navigate('/app/membership', { replace: true });
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          toast.error('No se pudo verificar el pago. Por favor contacta a soporte.');
          setProcessingPayment(false);
        }
      } catch (error) {
        console.error('Error checking payment:', error);
        setProcessingPayment(false);
      }
    };

    poll();
  };

  const checkRedsysResult = async (result, orderNumber) => {
    setProcessingPayment(true);
    if (result === 'ok') {
      // Poll for confirmation from backend notification
      let attempts = 0;
      const poll = async () => {
        try {
          const res = await getRedsysPaymentStatus(orderNumber);
          if (res.data.payment_status === 'paid') {
            toast.success('Pago exitoso! Tu membresia ha sido activada');
            await refreshMemberData();
            navigate('/app/membership', { replace: true });
            setProcessingPayment(false);
            return;
          }
          attempts++;
          if (attempts < 10) {
            setTimeout(poll, 2000);
          } else {
            toast.success('Pago procesado. Tu membresia se activara en unos minutos.');
            setProcessingPayment(false);
            navigate('/app/membership', { replace: true });
          }
        } catch {
          setProcessingPayment(false);
        }
      };
      poll();
    } else {
      toast.error('El pago no se ha completado. Intentalo de nuevo.');
      setProcessingPayment(false);
      navigate('/app/membership', { replace: true });
    }
  };

  const handleSelectPlan = async (planId) => {
    try {
      setProcessingPayment(true);
      // Check which gateway is active for this gym
      const API = process.env.REACT_APP_BACKEND_URL + '/api';
      const gwRes = await axios.get(`${API}/gyms/${gym?.id}/has-payments`);
      const gateway = gwRes.data?.gateway || 'none';

      if (gateway === 'redsys') {
        const redsysRes = await initiateRedsysPayment({ member_id: member?.id, plan_id: planId, gym_id: gym?.id });
        if (redsysRes.data?.redsys_url) {
          // Detect PWABuilder / standalone PWA on iOS. In WKWebView the Redsys WAF
          // blocks the request (missing third-party cookies/referers), so we need
          // the user to open the payment in the system Safari browser via a
          // user-gesture <a target="_blank"> click. Our backend exposes a public
          // GET /api/redsys/pay/{order_number} page that auto-submits the POST
          // form to Redsys from the external browser context.
          const isStandalone = window.matchMedia('(display-mode: standalone)').matches
            || window.navigator.standalone === true
            || /pwabuilder/i.test(navigator.userAgent || '');

          const payUrl = redsysRes.data.pay_url;

          if (isStandalone && payUrl) {
            // Show a visible button so the user physically taps -> iOS opens in Safari
            setRedsysPayUrl(payUrl);
            setProcessingPayment(false);
            toast.info('Pulsa "Abrir pago seguro" para continuar en Safari');
            return;
          }

          if (payUrl) {
            // Normal browser: full-page navigation to the auto-submitting page
            window.location.href = payUrl;
            return;
          }

          // Last-resort fallback: inline POST form submission
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = redsysRes.data.redsys_url;
          Object.entries({
            'Ds_SignatureVersion': redsysRes.data.Ds_SignatureVersion,
            'Ds_MerchantParameters': redsysRes.data.Ds_MerchantParameters,
            'Ds_Signature': redsysRes.data.Ds_Signature,
          }).forEach(([name, value]) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            input.value = value;
            form.appendChild(input);
          });
          document.body.appendChild(form);
          form.submit();
          return;
        }
      } else if (gateway === 'stripe') {
        const response = await createCheckout(planId);
        window.location.href = response.data.url;
        return;
      } else if (gateway === 'mercadopago') {
        const response = await createCheckout(planId);
        window.location.href = response.data.url;
        return;
      } else {
        toast.error('Este gimnasio no tiene pagos en linea habilitados');
        setProcessingPayment(false);
        return;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al iniciar el pago');
      setProcessingPayment(false);
    }
  };

  const getDurationLabel = (days) => {
    if (days === 1) return '1 día';
    if (days === 7) return '1 semana';
    if (days === 30) return '1 mes';
    if (days === 90) return '3 meses';
    if (days === 180) return '6 meses';
    if (days === 365) return '1 año';
    return `${days} días`;
  };

  if (processingPayment) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center">
        <Loader2 size={48} className="animate-spin mb-4" style={{ color: 'var(--gym-primary)' }} />
        <p className="text-lg font-medium">Procesando pago...</p>
        <p className="text-zinc-500 text-sm">Por favor espera</p>
      </div>
    );
  }

  return (
    <div className="space-y-5 sm:space-y-6" data-testid="member-membership">
      {/* Redsys external-browser modal (shown on iOS PWA so Redsys WAF/3DS/cookies work) */}
      {redsysPayUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" data-testid="redsys-external-modal">
          <div className="w-full max-w-sm rounded-2xl bg-zinc-900 border border-zinc-800 p-6 text-center shadow-2xl">
            <div className="mx-auto mb-4 w-14 h-14 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(197,248,42,0.15)' }}>
              <CreditCard size={28} style={{ color: 'var(--gym-primary, #c5f82a)' }} />
            </div>
            <h3 className="text-lg font-black mb-2">Pago seguro</h3>
            <p className="text-sm text-zinc-400 mb-5">
              Para completar el pago de forma segura, abriremos la pasarela Redsys en Safari.
              Al terminar, vuelve a esta app para ver el resultado.
            </p>
            <a
              href={redsysPayUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => { setTimeout(() => setRedsysPayUrl(null), 500); }}
              className="block w-full py-3 rounded-xl font-black text-base text-black"
              style={{ backgroundColor: 'var(--gym-primary, #c5f82a)' }}
              data-testid="redsys-open-safari-btn"
            >
              Abrir pago seguro
            </a>
            <button
              onClick={() => setRedsysPayUrl(null)}
              className="mt-3 w-full py-2 text-xs text-zinc-500 hover:text-zinc-300"
              data-testid="redsys-cancel-btn"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div>
        <h1 className="text-xl sm:text-2xl font-black tracking-tight">Mi Membresía</h1>
        <p className="text-zinc-400 text-xs sm:text-sm">Gestiona tu plan y pagos</p>
      </div>

      {/* Current Membership */}
      {membership ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`stat-card border-2 ${
            membershipStatus.color === 'success' ? 'border-emerald-500/30' :
            membershipStatus.color === 'warning' ? 'border-amber-500/30' : 'border-red-500/30'
          }`}
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-zinc-500 text-sm">Plan Actual</p>
              <h3 className="text-xl font-bold">{plan?.name || 'Membresía'}</h3>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              membershipStatus.color === 'success' ? 'bg-emerald-500/10 text-emerald-500' :
              membershipStatus.color === 'warning' ? 'bg-amber-500/10 text-amber-500' : 'bg-red-500/10 text-red-500'
            }`}>
              {membershipStatus.label}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center">
                <Calendar size={20} className="text-zinc-400" />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Vence</p>
                <p className="font-medium">{formatDate(membership.end_date)}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center">
                <Clock size={20} className="text-zinc-400" />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Restante</p>
                <p className="font-medium">
                  {daysRemaining > 0 ? `${daysRemaining} días` : 'Vencida'}
                </p>
              </div>
            </div>
          </div>

          {membershipStatus.status !== 'active' && (
            <div className="mt-4 p-3 rounded-xl bg-amber-500/10 flex items-center gap-3">
              <AlertTriangle size={18} className="text-amber-500 shrink-0" />
              <p className="text-sm text-amber-200">
                {membershipStatus.status === 'expired' 
                  ? 'Tu membresía ha vencido. Renueva para seguir accediendo.'
                  : 'Tu membresía está por vencer. Renueva ahora.'}
              </p>
            </div>
          )}
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="stat-card border-2 border-zinc-700"
        >
          <div className="text-center py-4">
            <CreditCard size={48} className="mx-auto text-zinc-600 mb-4" />
            <h3 className="text-lg font-bold mb-1">Sin Membresía Activa</h3>
            <p className="text-zinc-500 text-sm">Selecciona un plan para comenzar</p>
          </div>
        </motion.div>
      )}

      {/* Available Plans */}
      <div>
        <h2 className="text-lg font-bold mb-4">
          {membership ? 'Renovar Membresía' : 'Planes Disponibles'}
        </h2>
        
        {loading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="stat-card">
                <div className="skeleton h-6 w-32 mb-2" />
                <div className="skeleton h-8 w-24" />
              </div>
            ))}
          </div>
        ) : plans.length === 0 ? (
          <div className="text-center py-8 text-zinc-500">
            No hay planes disponibles
          </div>
        ) : (
          <div className="space-y-4">
            {plans.map((p, index) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="stat-card hover:border-zinc-600 transition-colors"
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-lg">{p.name}</h3>
                    <p className="text-zinc-500 text-sm">{getDurationLabel(p.duration_days)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-black" style={{ color: 'var(--gym-primary)' }}>
                      {formatCurrency(p.price)}
                    </p>
                  </div>
                </div>
                
                {p.description && (
                  <p className="text-zinc-400 text-sm mb-4">{p.description}</p>
                )}

                <Button
                  onClick={() => handleSelectPlan(p.id)}
                  className="w-full btn-gym-primary"
                  data-testid={`select-plan-${p.id}`}
                >
                  <CreditCard size={18} className="mr-2" />
                  Seleccionar Plan
                </Button>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
