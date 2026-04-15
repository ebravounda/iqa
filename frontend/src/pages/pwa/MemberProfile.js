import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { formatDate } from '../../lib/utils';
import { motion } from 'framer-motion';
import { User, Mail, Phone, Calendar, QrCode, Share2, Download, Camera, Loader2 } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';
import { uploadAvatar } from '../../lib/api';

export default function MemberProfile() {
  const { member, gym, logout, refreshMemberData } = useAuth();
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [canInstall, setCanInstall] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [avatarKey, setAvatarKey] = useState(Date.now());
  const fileInputRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setCanInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setCanInstall(false);
    }

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) {
      toast.info('Para instalar, usa el menú de tu navegador');
      return;
    }
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      toast.success('¡App instalada correctamente!');
      setCanInstall(false);
    }
    setDeferredPrompt(null);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${gym?.name} - Mi QR de Acceso`,
          text: `Accede a ${gym?.name} con mi codigo: ${member?.code}`,
          url: window.location.origin + '/app'
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      navigator.clipboard.writeText(`${gym?.name} - Codigo: ${member?.code}`);
      toast.success('Informacion copiada al portapapeles');
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      toast.error('La imagen no puede superar 2MB');
      return;
    }
    setUploading(true);
    try {
      const res = await uploadAvatar(file);
      toast.success('Foto actualizada');
      setAvatarKey(Date.now());
      if (refreshMemberData) await refreshMemberData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al subir foto');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-5 sm:space-y-6" data-testid="member-profile">
      <div>
        <h1 className="text-xl sm:text-2xl font-black tracking-tight">Mi Perfil</h1>
        <p className="text-zinc-400 text-xs sm:text-sm">Información de tu cuenta</p>
      </div>

      {/* Profile Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="stat-card"
      >
        <div className="flex items-center gap-4 mb-6">
          <div className="relative">
            {member?.avatar_url ? (
              <img 
                src={`${member.avatar_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${member.avatar_url}` : member.avatar_url}?v=${avatarKey}`} 
                alt={member.name}
                className="w-20 h-20 rounded-2xl object-cover"
              />
            ) : (
              <div 
                className="w-20 h-20 rounded-2xl flex items-center justify-center font-black text-3xl"
                style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
              >
                {member?.name?.charAt(0)}
              </div>
            )}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center border-2 border-zinc-900 transition-colors"
              style={{ backgroundColor: 'var(--gym-primary)', color: '#000' }}
              data-testid="upload-avatar-btn"
            >
              {uploading ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleAvatarUpload}
            />
          </div>
          <div>
            <h2 className="text-xl font-bold">{member?.name}</h2>
            <p className="font-mono text-lg" style={{ color: 'var(--gym-primary)' }}>
              {member?.code}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-4 py-3 border-b border-zinc-800">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center">
              <Mail size={18} className="text-zinc-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Email</p>
              <p className="font-medium">{member?.email}</p>
            </div>
          </div>
          
          {member?.phone && (
            <div className="flex items-center gap-4 py-3 border-b border-zinc-800">
              <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center">
                <Phone size={18} className="text-zinc-400" />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Teléfono</p>
                <p className="font-medium">{member?.phone}</p>
              </div>
            </div>
          )}
          
          <div className="flex items-center gap-4 py-3">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center">
              <Calendar size={18} className="text-zinc-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Miembro desde</p>
              <p className="font-medium">{formatDate(member?.created_at)}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Gym Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="stat-card"
      >
        <div className="flex items-center gap-4">
          {gym?.logo_url ? (
            <img 
              src={gym.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${gym.logo_url}` : gym.logo_url} 
              alt={gym.name}
              className="h-14 max-w-[140px] object-contain"
            />
          ) : (
            <div 
              className="w-14 h-14 rounded-xl flex items-center justify-center font-black text-xl"
              style={{ backgroundColor: 'var(--gym-primary)', color: 'var(--gym-primary-foreground)' }}
            >
              {gym?.name?.charAt(0)}
            </div>
          )}
          <div>
            <p className="text-xs text-zinc-500">Mi Gimnasio</p>
            <h3 className="font-bold text-lg">{gym?.name}</h3>
            {gym?.address && <p className="text-sm text-zinc-400">{gym.address}</p>}
          </div>
        </div>
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="space-y-3"
      >
        {canInstall && (
          <Button
            onClick={handleInstall}
            className="w-full btn-gym-primary"
            data-testid="install-app-btn"
          >
            <Download size={18} className="mr-2" />
            Crear Acceso Directo
          </Button>
        )}

        <Button
          onClick={handleShare}
          variant="outline"
          className="w-full border-zinc-700 hover:bg-zinc-800"
          data-testid="share-btn"
        >
          <Share2 size={18} className="mr-2" />
          Compartir
        </Button>

        <Button
          onClick={logout}
          variant="ghost"
          className="w-full text-red-500 hover:text-red-400 hover:bg-red-500/10"
          data-testid="logout-btn"
        >
          Cerrar Sesión
        </Button>
      </motion.div>

      {/* App Info */}
      <div className="text-center text-xs text-zinc-600 pt-4">
        <p>IngresoQR v1.2.19</p>
        <p>© {new Date().getFullYear()} Todos los derechos reservados</p>
      </div>
    </div>
  );
}
