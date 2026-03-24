import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getGym, updateGym, getStripeConfig, updateStripeConfig } from '../../lib/api';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Save, Palette, Clock, CreditCard, Eye, EyeOff, CheckCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminSettings() {
  const { admin, isSuperAdmin } = useAuth();
  const [gym, setGym] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
    logo_url: '',
    primary_color: '#E1FF01',
    qr_refresh_seconds: 10
  });

  // Stripe config state
  const [stripeData, setStripeData] = useState({
    stripe_secret_key: '',
    stripe_currency: 'usd'
  });
  const [stripeStatus, setStripeStatus] = useState({ has_stripe_key: false, masked_key: '' });
  const [showStripeKey, setShowStripeKey] = useState(false);
  const [savingStripe, setSavingStripe] = useState(false);

  useEffect(() => {
    if (admin?.gym_id) {
      fetchGym();
      fetchStripeConfig();
    } else {
      setLoading(false);
    }
  }, [admin]);

  const fetchGym = async () => {
    try {
      const response = await getGym(admin.gym_id);
      setGym(response.data);
      setFormData({
        name: response.data.name || '',
        address: response.data.address || '',
        phone: response.data.phone || '',
        email: response.data.email || '',
        logo_url: response.data.logo_url || '',
        primary_color: response.data.primary_color || '#E1FF01',
        qr_refresh_seconds: response.data.qr_refresh_seconds || 10
      });
    } catch (error) {
      toast.error('Error al cargar configuración');
    } finally {
      setLoading(false);
    }
  };

  const fetchStripeConfig = async () => {
    try {
      const response = await getStripeConfig(admin.gym_id);
      setStripeStatus(response.data);
      setStripeData(prev => ({ ...prev, stripe_currency: response.data.currency || 'usd' }));
    } catch (error) {
      console.error('Error fetching stripe config:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const cleanData = {};
      for (const [key, value] of Object.entries(formData)) {
        if (value !== '' && value !== null && value !== undefined) {
          cleanData[key] = value;
        }
      }
      await updateGym(admin.gym_id, cleanData);
      toast.success('Configuración guardada');
      document.documentElement.style.setProperty('--gym-primary', formData.primary_color);
    } catch (error) {
      toast.error('Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveStripe = async () => {
    if (!stripeData.stripe_secret_key && !stripeStatus.has_stripe_key) {
      toast.error('Ingresa tu clave secreta de Stripe');
      return;
    }
    setSavingStripe(true);
    try {
      const payload = { stripe_currency: stripeData.stripe_currency };
      if (stripeData.stripe_secret_key) {
        payload.stripe_secret_key = stripeData.stripe_secret_key;
      }
      await updateStripeConfig(admin.gym_id, payload);
      toast.success('Configuración de pagos guardada');
      setStripeData(prev => ({ ...prev, stripe_secret_key: '' }));
      fetchStripeConfig();
    } catch (error) {
      toast.error('Error al guardar configuración de pagos');
    } finally {
      setSavingStripe(false);
    }
  };

  const presetColors = [
    '#E1FF01', '#FF6B6B', '#4ECDC4', '#45B7D1',
    '#96CEB4', '#FFEAA7', '#DDA0DD', '#FF8C00',
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="stat-card">
          <div className="skeleton h-4 w-32 mb-4" />
          <div className="skeleton h-10 w-full" />
        </div>
      </div>
    );
  }

  if (!admin?.gym_id && !isSuperAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-zinc-500">No tienes un gimnasio asignado</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-settings">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Configuración del Gimnasio</h1>
        <p className="text-zinc-400 text-sm">Personaliza tu gimnasio y configura opciones</p>
      </div>

      {/* Stripe / Payment Gateway Configuration */}
      <div className="stat-card border-2 border-zinc-700/50">
        <div className="flex items-center gap-2 mb-6">
          <CreditCard size={20} className="text-blue-400" />
          <h3 className="font-bold text-lg">Pasarela de Pagos (Stripe)</h3>
        </div>

        <div className="flex items-center gap-3 mb-6 p-3 rounded-xl bg-zinc-800/50">
          {stripeStatus.has_stripe_key ? (
            <>
              <CheckCircle size={20} className="text-emerald-500 shrink-0" />
              <div>
                <p className="font-medium text-emerald-400">Stripe Configurado</p>
                <p className="text-xs text-zinc-500">Clave: {stripeStatus.masked_key}</p>
              </div>
            </>
          ) : (
            <>
              <AlertTriangle size={20} className="text-amber-500 shrink-0" />
              <div>
                <p className="font-medium text-amber-400">Stripe No Configurado</p>
                <p className="text-xs text-zinc-500">Los socios no podrán realizar pagos en línea</p>
              </div>
            </>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">
              Clave Secreta de Stripe {stripeStatus.has_stripe_key && '(dejar vacío para mantener la actual)'}
            </label>
            <div className="relative">
              <Input
                type={showStripeKey ? 'text' : 'password'}
                value={stripeData.stripe_secret_key}
                onChange={(e) => setStripeData({ ...stripeData, stripe_secret_key: e.target.value })}
                placeholder={stripeStatus.has_stripe_key ? 'Clave actual guardada' : 'sk_live_... o sk_test_...'}
                className="input-dark pr-10"
                data-testid="stripe-key-input"
              />
              <button
                type="button"
                onClick={() => setShowStripeKey(!showStripeKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
              >
                {showStripeKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              Obtén tu clave en <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">dashboard.stripe.com/apikeys</a>
            </p>
          </div>

          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Moneda</label>
            <Select
              value={stripeData.stripe_currency}
              onValueChange={(v) => setStripeData({ ...stripeData, stripe_currency: v })}
            >
              <SelectTrigger className="w-[200px] bg-zinc-800 border-zinc-700" data-testid="stripe-currency-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                <SelectItem value="usd">USD (Dólar)</SelectItem>
                <SelectItem value="eur">EUR (Euro)</SelectItem>
                <SelectItem value="mxn">MXN (Peso Mexicano)</SelectItem>
                <SelectItem value="ars">ARS (Peso Argentino)</SelectItem>
                <SelectItem value="clp">CLP (Peso Chileno)</SelectItem>
                <SelectItem value="cop">COP (Peso Colombiano)</SelectItem>
                <SelectItem value="pen">PEN (Sol Peruano)</SelectItem>
                <SelectItem value="brl">BRL (Real Brasileño)</SelectItem>
                <SelectItem value="gbp">GBP (Libra Esterlina)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleSaveStripe} disabled={savingStripe} className="btn-gym-primary" data-testid="save-stripe-btn">
            <CreditCard size={18} className="mr-2" />
            {savingStripe ? 'Guardando...' : 'Guardar Configuración de Pagos'}
          </Button>
        </div>
      </div>

      {/* General Info */}
      <div className="stat-card">
        <h3 className="font-bold text-lg mb-6">Información General</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Nombre del Gimnasio</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-dark"
              data-testid="gym-name-input"
            />
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Email</label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="input-dark"
            />
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Teléfono</label>
            <Input
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="input-dark"
            />
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Dirección</label>
            <Input
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="input-dark"
            />
          </div>
        </div>
      </div>

      {/* Branding */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-6">
          <Palette size={20} style={{ color: formData.primary_color }} />
          <h3 className="font-bold text-lg">Marca y Colores</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">URL del Logo</label>
            <div className="flex gap-3">
              <Input
                value={formData.logo_url}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                placeholder="https://..."
                className="input-dark flex-1"
              />
              {formData.logo_url && (
                <img src={formData.logo_url} alt="Logo" className="w-10 h-10 rounded-lg object-cover" />
              )}
            </div>
          </div>
          
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Color Principal</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="w-10 h-10 rounded-lg cursor-pointer border-0"
              />
              <Input
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="input-dark flex-1 font-mono"
                data-testid="primary-color-input"
              />
            </div>
            <div className="flex gap-2 mt-3 flex-wrap">
              {presetColors.map((color) => (
                <button
                  key={color}
                  onClick={() => setFormData({ ...formData, primary_color: color })}
                  className={`w-8 h-8 rounded-full transition-transform hover:scale-110 ${
                    formData.primary_color === color ? 'ring-2 ring-white ring-offset-2 ring-offset-zinc-900' : ''
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Preview */}
        <div className="mt-6 p-4 rounded-xl bg-zinc-800/50 border border-zinc-700">
          <p className="text-sm text-zinc-400 mb-3">Vista previa</p>
          <div className="flex items-center gap-4">
            <div 
              className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl"
              style={{ backgroundColor: formData.primary_color, color: '#000' }}
            >
              {formData.name?.charAt(0) || 'G'}
            </div>
            <div>
              <p className="font-bold">{formData.name || 'Mi Gimnasio'}</p>
              <p className="text-sm" style={{ color: formData.primary_color }}>Color de acento</p>
            </div>
          </div>
        </div>
      </div>

      {/* QR Settings */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-6">
          <Clock size={20} className="text-blue-400" />
          <h3 className="font-bold text-lg">Configuración del QR</h3>
        </div>
        
        <div>
          <label className="text-sm text-zinc-400 mb-2 block">Tiempo de Refresco del QR (segundos)</label>
          <Select 
            value={formData.qr_refresh_seconds.toString()} 
            onValueChange={(v) => setFormData({ ...formData, qr_refresh_seconds: parseInt(v) })}
          >
            <SelectTrigger className="w-[200px] bg-zinc-800 border-zinc-700" data-testid="qr-refresh-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-700">
              <SelectItem value="5">5 segundos (máxima seguridad)</SelectItem>
              <SelectItem value="10">10 segundos (recomendado)</SelectItem>
              <SelectItem value="15">15 segundos</SelectItem>
              <SelectItem value="30">30 segundos</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-zinc-500 mt-2">
            El QR del socio cambiará cada {formData.qr_refresh_seconds} segundos para mayor seguridad
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving} className="btn-gym-primary" data-testid="save-settings-btn">
          <Save size={20} className="mr-2" />
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </Button>
      </div>
    </div>
  );
}
