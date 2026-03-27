import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getGym, updateGym, getStripeConfig, updateStripeConfig, getMercadoPagoConfig, updateMercadoPagoConfig, updateMaxDevices } from '../../lib/api';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Save, Palette, Clock, CreditCard, Eye, EyeOff, CheckCircle, AlertTriangle, Link2, Copy, Mail, Send, Loader2, Globe, Smartphone, UserCog } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

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
    qr_refresh_seconds: 10,
    qr_mode: 'dynamic'
  });

  // Stripe config state
  const [stripeData, setStripeData] = useState({
    stripe_secret_key: '',
    stripe_currency: 'usd'
  });
  const [stripeStatus, setStripeStatus] = useState({ has_stripe_key: false, masked_key: '' });
  const [showStripeKey, setShowStripeKey] = useState(false);
  const [savingStripe, setSavingStripe] = useState(false);

  // SMTP config state
  const [smtpData, setSmtpData] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: ''
  });
  const [savingSmtp, setSavingSmtp] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);

  // MercadoPago config
  const [mpData, setMpData] = useState({ mercadopago_access_token: '' });
  const [mpStatus, setMpStatus] = useState({ has_mercadopago: false, masked_token: '' });
  const [showMpKey, setShowMpKey] = useState(false);
  const [savingMp, setSavingMp] = useState(false);

  // Currency
  const [gymCurrency, setGymCurrency] = useState('EUR');
  const [maxDevices, setMaxDevices] = useState(2);
  const [savingDevices, setSavingDevices] = useState(false);

  // Account settings (Super Admin)
  const [accountData, setAccountData] = useState({ email: '', password: '', current_password: '' });
  const [savingAccount, setSavingAccount] = useState(false);
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);

  useEffect(() => {
    if (admin?.gym_id) {
      fetchGym();
      fetchStripeConfig();
      fetchMpConfig();
    } else {
      setLoading(false);
    }
    if (admin?.email) {
      setAccountData(prev => ({ ...prev, email: admin.email }));
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
        qr_refresh_seconds: response.data.qr_refresh_seconds || 10,
        qr_mode: response.data.qr_mode || 'dynamic'
      });
      setSmtpData({
        smtp_host: response.data.smtp_host || '',
        smtp_port: response.data.smtp_port || 587,
        smtp_user: response.data.smtp_user || '',
        smtp_password: response.data.smtp_password || '',
        smtp_from_email: response.data.smtp_from_email || ''
      });
      setGymCurrency(response.data.currency || 'EUR');
      setMaxDevices(response.data.max_devices_per_member || 2);
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

  const fetchMpConfig = async () => {
    try {
      const response = await getMercadoPagoConfig(admin.gym_id);
      setMpStatus(response.data);
    } catch (error) {
      console.error('Error fetching MP config:', error);
    }
  };

  const handleSaveMp = async () => {
    if (!mpData.mercadopago_access_token && !mpStatus.has_mercadopago) {
      toast.error('Ingresa tu Access Token de MercadoPago');
      return;
    }
    setSavingMp(true);
    try {
      const payload = {};
      if (mpData.mercadopago_access_token) payload.mercadopago_access_token = mpData.mercadopago_access_token;
      await updateMercadoPagoConfig(admin.gym_id, payload);
      toast.success('Configuracion de MercadoPago guardada');
      setMpData({ mercadopago_access_token: '' });
      fetchMpConfig();
    } catch (error) {
      toast.error('Error al guardar MercadoPago');
    } finally { setSavingMp(false); }
  };

  const handleSaveCurrency = async () => {
    try {
      await updateGym(admin.gym_id, { currency: gymCurrency });
      toast.success('Moneda actualizada');
    } catch (error) { toast.error('Error al guardar moneda'); }
  };

  const handleSaveAccount = async () => {
    if (!accountData.current_password) {
      toast.error('Debes ingresar tu contraseña actual');
      return;
    }
    if (!accountData.email && !accountData.password) {
      toast.error('Ingresa un nuevo email o contraseña');
      return;
    }
    setSavingAccount(true);
    try {
      const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const res = await axios.put(`${API_URL}/auth/admin/update-profile`, {
        email: accountData.email,
        password: accountData.password,
        current_password: accountData.current_password
      });
      toast.success(res.data.message);
      if (res.data.token) {
        localStorage.setItem('token', res.data.token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.token}`;
      }
      if (res.data.admin) {
        localStorage.setItem('admin', JSON.stringify(res.data.admin));
      }
      setAccountData(prev => ({ ...prev, password: '', current_password: '' }));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al actualizar perfil');
    } finally {
      setSavingAccount(false);
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
        <h1 className="text-2xl font-black tracking-tight">Configuracion</h1>
        <p className="text-zinc-400 text-sm">{admin?.gym_id ? 'Personaliza tu gimnasio y configura opciones' : 'Administra tu cuenta'}</p>
      </div>

      {/* My Account Section */}
      {isSuperAdmin && !admin?.gym_id && (
        <div className="stat-card border-2 border-zinc-700/50">
          <div className="flex items-center gap-2 mb-6">
            <UserCog size={20} style={{ color: 'var(--gym-primary)' }} />
            <h3 className="font-bold text-lg">Mi Cuenta (Super Admin)</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">Email</label>
              <Input
                type="email"
                value={accountData.email}
                onChange={(e) => setAccountData({ ...accountData, email: e.target.value })}
                className="input-dark"
                data-testid="account-email-input"
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">Nueva Contraseña <span className="text-zinc-600">(dejar vacio para no cambiar)</span></label>
              <div className="relative">
                <Input
                  type={showNewPw ? 'text' : 'password'}
                  value={accountData.password}
                  onChange={(e) => setAccountData({ ...accountData, password: e.target.value })}
                  placeholder="Min. 6 caracteres"
                  className="input-dark pr-10"
                  data-testid="account-new-password-input"
                />
                <button type="button" onClick={() => setShowNewPw(!showNewPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
                  {showNewPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div className="md:col-span-2">
              <label className="text-sm text-zinc-400 mb-2 block">Contraseña Actual <span className="text-red-400">*</span></label>
              <div className="relative">
                <Input
                  type={showCurrentPw ? 'text' : 'password'}
                  value={accountData.current_password}
                  onChange={(e) => setAccountData({ ...accountData, current_password: e.target.value })}
                  placeholder="Ingresa tu contraseña actual para confirmar"
                  className="input-dark pr-10"
                  data-testid="account-current-password-input"
                />
                <button type="button" onClick={() => setShowCurrentPw(!showCurrentPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
                  {showCurrentPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          </div>
          <Button onClick={handleSaveAccount} disabled={savingAccount} className="btn-gym-primary mt-6" data-testid="save-account-btn">
            <Save size={16} className="mr-2" />
            {savingAccount ? 'Guardando...' : 'Guardar Cambios de Cuenta'}
          </Button>
        </div>
      )}

      {/* Gym-specific settings only if gym_id exists */}
      {!admin?.gym_id && !isSuperAdmin && (
        <div className="text-center py-12">
          <p className="text-zinc-500">No tienes un gimnasio asignado</p>
        </div>
      )}

      {admin?.gym_id && (<>
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

      {/* Currency Configuration */}
      <div className="stat-card border-2 border-zinc-700/50">
        <div className="flex items-center gap-2 mb-6">
          <Globe size={20} className="text-emerald-400" />
          <h3 className="font-bold text-lg">Moneda del Gimnasio</h3>
        </div>
        <div className="flex items-center gap-4">
          <Select value={gymCurrency} onValueChange={setGymCurrency}>
            <SelectTrigger className="w-[250px] bg-zinc-800 border-zinc-700" data-testid="gym-currency-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-700">
              <SelectItem value="EUR">EUR - Euro</SelectItem>
              <SelectItem value="USD">USD - Dolar US</SelectItem>
              <SelectItem value="CLP">CLP - Peso Chileno (sin decimales)</SelectItem>
              <SelectItem value="ARS">ARS - Peso Argentino</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleSaveCurrency} className="btn-gym-primary" data-testid="save-currency-btn">
            <Save size={16} className="mr-2" /> Guardar
          </Button>
        </div>
        <p className="text-xs text-zinc-500 mt-2">La moneda afecta a todos los precios, pagos y reportes del gimnasio.</p>
      </div>

      {/* MercadoPago Configuration */}
      <div className="stat-card border-2 border-zinc-700/50">
        <div className="flex items-center gap-2 mb-6">
          <CreditCard size={20} className="text-sky-400" />
          <h3 className="font-bold text-lg">MercadoPago</h3>
          <span className="text-xs bg-sky-900/30 text-sky-400 px-2 py-0.5 rounded ml-2">Solo CLP</span>
        </div>
        <div className="flex items-center gap-3 mb-6 p-3 rounded-xl bg-zinc-800/50">
          {mpStatus.has_mercadopago ? (
            <>
              <CheckCircle size={20} className="text-emerald-500 shrink-0" />
              <div>
                <p className="font-medium text-emerald-400">MercadoPago Configurado</p>
                <p className="text-xs text-zinc-500">Token: {mpStatus.masked_token}</p>
              </div>
            </>
          ) : (
            <>
              <AlertTriangle size={20} className="text-amber-500 shrink-0" />
              <div>
                <p className="font-medium text-amber-400">MercadoPago No Configurado</p>
                <p className="text-xs text-zinc-500">Disponible para gimnasios con moneda CLP</p>
              </div>
            </>
          )}
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Access Token {mpStatus.has_mercadopago && '(dejar vacio para mantener)'}</label>
            <div className="relative">
              <Input
                type={showMpKey ? 'text' : 'password'}
                value={mpData.mercadopago_access_token}
                onChange={(e) => setMpData({ mercadopago_access_token: e.target.value })}
                placeholder={mpStatus.has_mercadopago ? 'Token actual guardado' : 'APP_USR-...'}
                className="input-dark pr-10"
                data-testid="mp-token-input"
              />
              <button type="button" onClick={() => setShowMpKey(!showMpKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
                {showMpKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <p className="text-xs text-zinc-500 mt-1">Obten tu Access Token en <a href="https://www.mercadopago.cl/developers/panel" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">mercadopago.cl/developers</a></p>
          </div>
          <Button onClick={handleSaveMp} disabled={savingMp} className="btn-gym-primary" data-testid="save-mp-btn">
            <CreditCard size={18} className="mr-2" />
            {savingMp ? 'Guardando...' : 'Guardar MercadoPago'}
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
        
        <div className="space-y-4">
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Modo del QR</label>
            <Select 
              value={formData.qr_mode} 
              onValueChange={(v) => setFormData({ ...formData, qr_mode: v })}
            >
              <SelectTrigger className="w-[300px] bg-zinc-800 border-zinc-700" data-testid="qr-mode-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                <SelectItem value="dynamic">Dinámico (cambia cada X segundos)</SelectItem>
                <SelectItem value="static">Estático (código fijo por socio)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-zinc-500 mt-2">
              {formData.qr_mode === 'dynamic' 
                ? 'El QR del socio cambiará periódicamente para mayor seguridad'
                : 'El QR del socio será fijo y no cambiará. Menos seguro pero más simple.'}
            </p>
          </div>

          {formData.qr_mode === 'dynamic' && (
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
            </div>
          )}
        </div>
      </div>

      {/* Device Limit */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-6">
          <Smartphone size={20} className="text-violet-400" />
          <h3 className="font-bold text-lg">Control de Dispositivos (App)</h3>
        </div>
        <p className="text-zinc-400 text-sm mb-4">
          Limita cuantos dispositivos puede usar cada socio para acceder a la app. Si un socio excede el limite, debera contactar a recepcion.
        </p>
        <div className="flex items-center gap-4">
          <Select value={maxDevices.toString()} onValueChange={(v) => setMaxDevices(parseInt(v))}>
            <SelectTrigger className="w-[200px] bg-zinc-800 border-zinc-700" data-testid="max-devices-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-700">
              <SelectItem value="1">1 dispositivo</SelectItem>
              <SelectItem value="2">2 dispositivos</SelectItem>
              <SelectItem value="3">3 dispositivos</SelectItem>
              <SelectItem value="5">5 dispositivos</SelectItem>
              <SelectItem value="10">10 dispositivos</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={async () => {
            setSavingDevices(true);
            try {
              await updateMaxDevices(admin.gym_id, maxDevices);
              toast.success(`Limite de dispositivos: ${maxDevices}`);
            } catch (e) { toast.error('Error'); }
            finally { setSavingDevices(false); }
          }} disabled={savingDevices} className="btn-gym-primary" data-testid="save-max-devices-btn">
            <Save size={16} className="mr-2" /> {savingDevices ? 'Guardando...' : 'Guardar'}
          </Button>
        </div>
        <p className="text-xs text-zinc-500 mt-2">Puedes desactivar dispositivos individuales desde el menu de cada socio (Socios → 3 puntitos → Dispositivos).</p>
      </div>

      {/* Public Registration & Kiosk Links */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <Link2 size={20} className="text-emerald-400" />
          <h3 className="font-bold text-lg">Enlaces Públicos</h3>
        </div>
        <p className="text-zinc-400 text-sm mb-4">
          Comparte estos enlaces para registro de socios.
        </p>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">Registro desde teléfono</label>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-zinc-800 px-4 py-3 rounded-lg font-mono text-sm text-emerald-400 overflow-x-auto" data-testid="public-register-link">
                {window.location.origin}/register/{admin?.gym_id}
              </code>
              <Button variant="outline" className="border-zinc-700 shrink-0" data-testid="copy-register-link-btn"
                onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/register/${admin?.gym_id}`); toast.success('Enlace copiado'); }}>
                <Copy size={18} />
              </Button>
            </div>
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">Modo Kiosko (pantalla táctil en recepción)</label>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-zinc-800 px-4 py-3 rounded-lg font-mono text-sm text-blue-400 overflow-x-auto" data-testid="kiosk-link">
                {window.location.origin}/kiosk/{admin?.gym_id}
              </code>
              <Button variant="outline" className="border-zinc-700 shrink-0" data-testid="copy-kiosk-link-btn"
                onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/kiosk/${admin?.gym_id}`); toast.success('Enlace del kiosko copiado'); }}>
                <Copy size={18} />
              </Button>
            </div>
            <p className="text-xs text-zinc-500 mt-1">Abre este enlace en la tablet/PC del kiosko en modo pantalla completa</p>
          </div>
        </div>
      </div>

      {/* SMTP Configuration */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-6">
          <Mail size={20} className="text-orange-400" />
          <h3 className="font-bold text-lg">Configuración de Email (SMTP)</h3>
        </div>
        <p className="text-zinc-400 text-sm mb-4">
          Configura tu servidor SMTP para enviar emails automáticos a tus socios (bienvenida, recordatorios, etc.)
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">Servidor SMTP</label>
            <Input
              value={smtpData.smtp_host}
              onChange={(e) => setSmtpData({ ...smtpData, smtp_host: e.target.value })}
              placeholder="smtp.gmail.com"
              className="input-dark"
              data-testid="smtp-host-input"
            />
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">Puerto</label>
            <Select 
              value={smtpData.smtp_port.toString()} 
              onValueChange={(v) => setSmtpData({ ...smtpData, smtp_port: parseInt(v) })}
            >
              <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="smtp-port-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                <SelectItem value="587">587 (TLS - Recomendado)</SelectItem>
                <SelectItem value="465">465 (SSL)</SelectItem>
                <SelectItem value="25">25 (Sin cifrado)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">Usuario SMTP</label>
            <Input
              value={smtpData.smtp_user}
              onChange={(e) => setSmtpData({ ...smtpData, smtp_user: e.target.value })}
              placeholder="tu@email.com"
              className="input-dark"
              data-testid="smtp-user-input"
            />
          </div>
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">Contraseña SMTP</label>
            <div className="relative">
              <Input
                type={showSmtpPassword ? 'text' : 'password'}
                value={smtpData.smtp_password}
                onChange={(e) => setSmtpData({ ...smtpData, smtp_password: e.target.value })}
                placeholder="Contraseña o App Password"
                className="input-dark pr-10"
                data-testid="smtp-password-input"
              />
              <Button
                variant="ghost" size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                onClick={() => setShowSmtpPassword(!showSmtpPassword)}
              >
                {showSmtpPassword ? <EyeOff size={14} /> : <Eye size={14} />}
              </Button>
            </div>
          </div>
          <div className="md:col-span-2">
            <label className="text-sm text-zinc-400 mb-1 block">Email remitente (From)</label>
            <Input
              value={smtpData.smtp_from_email}
              onChange={(e) => setSmtpData({ ...smtpData, smtp_from_email: e.target.value })}
              placeholder="noreply@tugimnasio.com (opcional, usa el usuario si está vacío)"
              className="input-dark"
              data-testid="smtp-from-input"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 mt-6">
          <Button 
            onClick={async () => {
              setSavingSmtp(true);
              try {
                const cleanSmtp = {};
                for (const [key, value] of Object.entries(smtpData)) {
                  if (value !== '' && value !== null && value !== undefined) {
                    cleanSmtp[key] = value;
                  }
                }
                await updateGym(admin.gym_id, cleanSmtp);
                toast.success('Configuración SMTP guardada');
              } catch (error) {
                toast.error('Error al guardar SMTP');
              } finally {
                setSavingSmtp(false);
              }
            }}
            disabled={savingSmtp}
            className="btn-gym-primary"
            data-testid="save-smtp-btn"
          >
            <Save size={16} className="mr-2" />
            {savingSmtp ? 'Guardando...' : 'Guardar SMTP'}
          </Button>
          
          <Button
            variant="outline"
            className="border-zinc-700"
            onClick={async () => {
              setTestingEmail(true);
              try {
                const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;
                const response = await fetch(`${API_URL}/email/test`, {
                  method: 'POST',
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                  }
                });
                const data = await response.json();
                if (response.ok) {
                  toast.success(data.message);
                } else {
                  toast.error(data.detail || 'Error al enviar email de prueba');
                }
              } catch (error) {
                toast.error('Error al enviar email de prueba');
              } finally {
                setTestingEmail(false);
              }
            }}
            disabled={testingEmail || !smtpData.smtp_host}
            data-testid="test-email-btn"
          >
            {testingEmail ? <Loader2 size={16} className="animate-spin mr-2" /> : <Send size={16} className="mr-2" />}
            Enviar Email de Prueba
          </Button>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving} className="btn-gym-primary" data-testid="save-settings-btn">
          <Save size={20} className="mr-2" />
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </Button>
      </div>
      </>)}
    </div>
  );
}
