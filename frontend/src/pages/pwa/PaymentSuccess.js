import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle } from 'lucide-react';

export default function PaymentSuccess() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    // Redirect to membership page with session_id for processing
    if (sessionId) {
      navigate(`/app/membership?session_id=${sessionId}`, { replace: true });
    } else {
      navigate('/app/membership', { replace: true });
    }
  }, [sessionId, navigate]);

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center">
      <CheckCircle size={64} className="mb-4" style={{ color: 'var(--gym-primary)' }} />
      <h1 className="text-2xl font-bold mb-2">¡Pago Exitoso!</h1>
      <p className="text-zinc-400">Redirigiendo...</p>
      <Loader2 className="animate-spin mt-4" size={24} />
    </div>
  );
}
