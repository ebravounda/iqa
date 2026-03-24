import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { generateQR } from '../../lib/api';
import { getMembershipStatus, getDaysRemaining } from '../../lib/utils';
import { QRCodeSVG } from 'qrcode.react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Maximize2, AlertTriangle, CheckCircle } from 'lucide-react';

export default function MemberHome() {
  const { member, gym, membership } = useAuth();
  const [qrCode, setQrCode] = useState('');
  const [expiresAt, setExpiresAt] = useState(0);
  const [refreshSeconds, setRefreshSeconds] = useState(10);
  const [countdown, setCountdown] = useState(0);
  const [loading, setLoading] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [error, setError] = useState(null);

  const fetchQR = useCallback(async () => {
    try {
      setError(null);
      const response = await generateQR();
      setQrCode(response.data.qr_code);
      setExpiresAt(response.data.expires_at);
      setRefreshSeconds(response.data.refresh_seconds);
      setCountdown(response.data.refresh_seconds);
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

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) {
      fetchQR();
      return;
    }

    const timer = setInterval(() => {
      setCountdown(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown, fetchQR]);

  const membershipStatus = getMembershipStatus(membership);
  const daysRemaining = membership ? getDaysRemaining(membership.end_date) : 0;

  // Calculate countdown ring
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (countdown / refreshSeconds) * circumference;

  const QRDisplay = ({ size = 200, showTimer = true }) => (
    <div className="relative">
      {/* Countdown Ring */}
      {showTimer && (
        <svg className="absolute -inset-4 w-[calc(100%+32px)] h-[calc(100%+32px)]" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#27272A"
            strokeWidth="2"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="var(--gym-primary)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
      )}
      
      {/* QR Code */}
      <AnimatePresence mode="wait">
        <motion.div
          key={qrCode}
          initial={{ opacity: 0, rotateY: 180 }}
          animate={{ opacity: 1, rotateY: 0 }}
          exit={{ opacity: 0, rotateY: -180 }}
          transition={{ duration: 0.3 }}
          className="bg-white p-4 rounded-2xl"
        >
          {qrCode ? (
            <QRCodeSVG
              value={qrCode}
              size={size}
              level="H"
              includeMargin={false}
              bgColor="#FFFFFF"
              fgColor="#000000"
            />
          ) : (
            <div style={{ width: size, height: size }} className="bg-zinc-200 animate-pulse rounded" />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );

  return (
    <div className="space-y-6" data-testid="member-home">
      {/* Membership Status Alert */}
      {membershipStatus.status !== 'active' && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-xl flex items-center gap-3 ${
            membershipStatus.status === 'expired' 
              ? 'bg-red-500/10 border border-red-500/20' 
              : 'bg-amber-500/10 border border-amber-500/20'
          }`}
        >
          <AlertTriangle size={20} className={membershipStatus.status === 'expired' ? 'text-red-500' : 'text-amber-500'} />
          <div className="flex-1">
            <p className={`font-medium text-sm ${membershipStatus.status === 'expired' ? 'text-red-500' : 'text-amber-500'}`}>
              {membershipStatus.label}
            </p>
            {membershipStatus.status === 'expired' && (
              <p className="text-xs text-zinc-400">Renueva tu membresía para acceder</p>
            )}
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
        {/* Member Info */}
        <div className="mb-6">
          <h2 className="text-xl font-bold">{member?.name}</h2>
          <p className="text-zinc-400 font-mono text-sm">{member?.code}</p>
        </div>

        {/* QR Code */}
        <div 
          className="flex justify-center cursor-pointer"
          onClick={() => setFullscreen(true)}
          data-testid="qr-expand-btn"
        >
          {loading ? (
            <div className="w-[200px] h-[200px] bg-zinc-800 rounded-2xl animate-pulse" />
          ) : error ? (
            <div className="w-[200px] h-[200px] bg-zinc-800 rounded-2xl flex items-center justify-center">
              <p className="text-red-500 text-sm">{error}</p>
            </div>
          ) : (
            <QRDisplay size={200} />
          )}
        </div>

        {/* Countdown */}
        <div className="mt-6 flex items-center justify-center gap-2">
          <span className="text-zinc-500 text-sm">Actualiza en</span>
          <span 
            className="font-mono font-bold text-lg"
            style={{ color: 'var(--gym-primary)' }}
            data-testid="qr-countdown"
          >
            {countdown}s
          </span>
        </div>

        {/* Expand button */}
        <button
          onClick={() => setFullscreen(true)}
          className="mt-4 text-zinc-400 hover:text-white flex items-center gap-2 mx-auto text-sm transition-colors"
        >
          <Maximize2 size={16} />
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
              <p className="font-mono text-lg" style={{ color: 'var(--gym-primary)' }}>
                Actualiza en {countdown}s
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
