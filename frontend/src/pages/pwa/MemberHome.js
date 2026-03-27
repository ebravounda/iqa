import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { generateQR } from '../../lib/api';
import { getMembershipStatus, getDaysRemaining } from '../../lib/utils';
import { QRCodeSVG } from 'qrcode.react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Maximize2, AlertTriangle, CheckCircle, CreditCard, BarChart3, Calendar, Clock, Trophy, Dumbbell } from 'lucide-react';
import { Button } from '../../components/ui/button';

export default function MemberHome() {
  const { member, gym, membership } = useAuth();
  const navigate = useNavigate();
  const [qrCode, setQrCode] = useState('');
  const [expiresAt, setExpiresAt] = useState(0);
  const [refreshSeconds, setRefreshSeconds] = useState(10);
  const [countdown, setCountdown] = useState(0);
  const [loading, setLoading] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [error, setError] = useState(null);
  const [qrMode, setQrMode] = useState('dynamic');

  const fetchQR = useCallback(async () => {
    try {
      setError(null);
      const response = await generateQR();
      setQrCode(response.data.qr_code);
      setExpiresAt(response.data.expires_at);
      setRefreshSeconds(response.data.refresh_seconds);
      setCountdown(response.data.refresh_seconds);
      setQrMode(response.data.qr_mode || 'dynamic');
      setLoading(false);
    } catch (err) {
      console.error('Error generating QR:', err);
      setError('Error al generar QR');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQR();
  }, [fetchQR]);

  // Countdown timer - only for dynamic QR
  useEffect(() => {
    if (qrMode === 'static') return;
    if (countdown <= 0) {
      fetchQR();
      return;
    }

    const timer = setInterval(() => {
      setCountdown(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown, fetchQR, qrMode]);

  const membershipStatus = getMembershipStatus(membership);
  const daysRemaining = membership ? getDaysRemaining(membership.end_date) : 0;

  // Calculate countdown ring
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (countdown / refreshSeconds) * circumference;

  const QRDisplay = ({ size = 200, showTimer = true }) => (
    <div className="relative">
      {showTimer && (
        <svg className="absolute -inset-4 w-[calc(100%+32px)] h-[calc(100%+32px)]" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="#27272A" strokeWidth="2" />
          <circle
            cx="50" cy="50" r="45" fill="none"
            stroke="var(--gym-primary)" strokeWidth="2" strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
      )}
      <AnimatePresence mode="wait">
        <motion.div
          key={qrCode}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className="bg-white p-4 rounded-2xl"
        >
          {qrCode ? (
            <QRCodeSVG value={qrCode} size={size} level="H" includeMargin={false} bgColor="#FFFFFF" fgColor="#000000" />
          ) : (
            <div style={{ width: size, height: size }} className="bg-zinc-200 animate-pulse rounded" />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );

  const showPaymentAlert = membershipStatus.status === 'expired' || membershipStatus.status === 'expiring';

  return (
    <div className="space-y-6" data-testid="member-home">
      {/* Payment Alert - Membership expiring or expired */}
      {showPaymentAlert && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-xl ${
            membershipStatus.status === 'expired' 
              ? 'bg-red-500/10 border border-red-500/30' 
              : 'bg-amber-500/10 border border-amber-500/30'
          }`}
          data-testid="payment-alert"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle size={22} className={`shrink-0 mt-0.5 ${
              membershipStatus.status === 'expired' ? 'text-red-500' : 'text-amber-500'
            }`} />
            <div className="flex-1">
              <p className={`font-bold text-sm ${
                membershipStatus.status === 'expired' ? 'text-red-400' : 'text-amber-400'
              }`}>
                {membershipStatus.status === 'expired' 
                  ? 'Tu membresía ha vencido'
                  : `Tu membresía vence en ${daysRemaining} días`
                }
              </p>
              <p className="text-xs text-zinc-400 mt-1">
                {membershipStatus.status === 'expired'
                  ? 'Renueva tu membresía para seguir accediendo al gimnasio.'
                  : 'Renueva ahora para no perder acceso.'}
              </p>
              <Button
                onClick={() => navigate('/app/membership')}
                className="mt-3 btn-gym-primary text-sm h-9"
                data-testid="pay-now-btn"
              >
                <CreditCard size={16} className="mr-2" />
                {membershipStatus.status === 'expired' ? 'Renovar Ahora' : 'Pagar Ahora'}
              </Button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Main QR Card */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="qr-container text-center"
        data-testid="qr-container"
      >
        <div className="mb-4 sm:mb-6">
          <h2 className="text-lg sm:text-xl font-bold">{member?.name}</h2>
          <p className="text-zinc-400 font-mono text-xs sm:text-sm">{member?.code}</p>
        </div>

        <div 
          className="flex justify-center cursor-pointer"
          onClick={() => setFullscreen(true)}
          data-testid="qr-expand-btn"
        >
          {loading ? (
            <div className="w-[180px] h-[180px] sm:w-[200px] sm:h-[200px] bg-zinc-800 rounded-2xl animate-pulse" />
          ) : error ? (
            <div className="w-[180px] h-[180px] sm:w-[200px] sm:h-[200px] bg-zinc-800 rounded-2xl flex items-center justify-center">
              <p className="text-red-500 text-sm">{error}</p>
            </div>
          ) : (
            <QRDisplay size={typeof window !== 'undefined' && window.innerWidth < 380 ? 160 : 200} />
          )}
        </div>

        {qrMode === 'dynamic' && (
          <div className="mt-4 sm:mt-6 flex items-center justify-center gap-2">
            <span className="text-zinc-500 text-xs sm:text-sm">Actualiza en</span>
            <span 
              className="font-mono font-bold text-base sm:text-lg"
              style={{ color: 'var(--gym-primary)' }}
              data-testid="qr-countdown"
            >
              {countdown}s
            </span>
          </div>
        )}
        {qrMode === 'static' && (
          <div className="mt-4 sm:mt-6 flex items-center justify-center gap-2">
            <span className="text-zinc-500 text-xs sm:text-sm">QR fijo - no caduca</span>
          </div>
        )}

        <button
          onClick={() => setFullscreen(true)}
          className="mt-3 sm:mt-4 text-zinc-400 hover:text-white flex items-center gap-2 mx-auto text-xs sm:text-sm transition-colors"
        >
          <Maximize2 size={14} />
          Pantalla completa
        </button>
      </motion.div>

      {/* Membership Info Card */}
      {membership && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="stat-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-zinc-500 text-sm">Tu Membresía</p>
              <p className="font-bold">{daysRemaining > 0 ? `${daysRemaining} días restantes` : 'Vencida'}</p>
            </div>
            <div className={`p-3 rounded-xl ${
              membershipStatus.color === 'success' ? 'bg-emerald-500/10' :
              membershipStatus.color === 'warning' ? 'bg-amber-500/10' : 'bg-red-500/10'
            }`}>
              <CheckCircle size={24} className={
                membershipStatus.color === 'success' ? 'text-emerald-500' :
                membershipStatus.color === 'warning' ? 'text-amber-500' : 'text-red-500'
              } />
            </div>
          </div>
        </motion.div>
      )}

      {/* No Membership Card */}
      {!membership && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="stat-card border border-amber-500/20"
        >
          <div className="text-center py-2">
            <CreditCard size={32} className="mx-auto text-amber-500 mb-3" />
            <p className="font-bold text-amber-400">Sin Membresía Activa</p>
            <p className="text-xs text-zinc-500 mt-1 mb-3">Necesitas una membresía para acceder</p>
            <Button onClick={() => navigate('/app/membership')} className="btn-gym-primary text-sm h-9" data-testid="get-membership-btn">
              <CreditCard size={16} className="mr-2" /> Ver Planes
            </Button>
          </div>
        </motion.div>
      )}

      {/* Quick Nav */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <div className="grid grid-cols-3 gap-3">
          <button onClick={() => navigate('/app/stats')} className="stat-card flex flex-col items-center gap-2 py-4 hover:border-[var(--gym-primary)]/30 transition-colors" data-testid="nav-stats">
            <BarChart3 size={22} className="text-[var(--gym-primary)]" />
            <span className="text-xs text-zinc-400">Estadisticas</span>
          </button>
          <button onClick={() => navigate('/app/achievements')} className="stat-card flex flex-col items-center gap-2 py-4 hover:border-[var(--gym-primary)]/30 transition-colors" data-testid="nav-achievements">
            <Trophy size={22} className="text-amber-400" />
            <span className="text-xs text-zinc-400">Logros</span>
          </button>
          <button onClick={() => navigate('/app/routines')} className="stat-card flex flex-col items-center gap-2 py-4 hover:border-[var(--gym-primary)]/30 transition-colors" data-testid="nav-routines">
            <Dumbbell size={22} className="text-purple-400" />
            <span className="text-xs text-zinc-400">Rutinas</span>
          </button>
        </div>
        <div className="grid grid-cols-3 gap-3 mt-3">
          <button onClick={() => navigate('/app/classes')} className="stat-card flex flex-col items-center gap-2 py-4 hover:border-[var(--gym-primary)]/30 transition-colors" data-testid="nav-classes">
            <Calendar size={22} className="text-emerald-400" />
            <span className="text-xs text-zinc-400">Clases</span>
          </button>
          <button onClick={() => navigate('/app/history')} className="stat-card flex flex-col items-center gap-2 py-4 hover:border-[var(--gym-primary)]/30 transition-colors" data-testid="nav-history">
            <Clock size={22} className="text-cyan-400" />
            <span className="text-xs text-zinc-400">Accesos</span>
          </button>
          <button onClick={() => navigate('/app/membership')} className="stat-card flex flex-col items-center gap-2 py-4 hover:border-[var(--gym-primary)]/30 transition-colors" data-testid="nav-membership">
            <CreditCard size={22} className="text-blue-400" />
            <span className="text-xs text-zinc-400">Membresia</span>
          </button>
        </div>
      </motion.div>

      {/* Fullscreen QR Modal */}
      <AnimatePresence>
        {fullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="qr-fullscreen"
            onClick={() => setFullscreen(false)}
            data-testid="qr-fullscreen-modal"
          >
            <button
              onClick={() => setFullscreen(false)}
              className="absolute top-6 right-6 p-3 rounded-full bg-zinc-800 hover:bg-zinc-700 transition-colors"
              data-testid="close-fullscreen-btn"
            >
              <X size={24} />
            </button>

            <div className="text-center mb-8">
              {gym?.logo_url ? (
                <img src={gym.logo_url} alt={gym?.name} className="w-16 h-16 rounded-xl mx-auto mb-4 object-cover" />
              ) : (
                <div 
                  className="w-16 h-16 rounded-xl mx-auto mb-4 flex items-center justify-center font-black text-2xl"
                  style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
                >
                  {gym?.name?.charAt(0)}
                </div>
              )}
              <h2 className="text-xl font-bold">{member?.name}</h2>
              <p className="text-zinc-400 font-mono">{member?.code}</p>
            </div>

            <div onClick={(e) => e.stopPropagation()}>
              <QRDisplay size={280} />
            </div>

            <div className="mt-8 text-center">
              <p className="text-zinc-500 text-sm mb-1">Muestra este código en el escáner</p>
              {qrMode === 'dynamic' ? (
                <p className="font-mono text-lg" style={{ color: 'var(--gym-primary)' }}>
                  Actualiza en {countdown}s
                </p>
              ) : (
                <p className="text-sm text-zinc-400">QR fijo - no caduca</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
