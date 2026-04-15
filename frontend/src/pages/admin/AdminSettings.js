import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useBusiness } from '../../context/BusinessContext';
import { getGym, updateGym, getStripeConfig, updateStripeConfig, getMercadoPagoConfig, updateMercadoPagoConfig, updateMaxDevices, getMySubscription, getAvailableSaaSPlans, subscribeSaaSPlan, getRedsysConfig, updateRedsysConfig, getPaymentGateway, setPaymentGateway } from '../../lib/api';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Save, Palette, Clock, CreditCard, Eye, EyeOff, CheckCircle, AlertTriangle, Link2, Copy, Mail, Send, Loader2, Globe, Smartphone, UserCog, Crown, QrCode, Users, Calendar, ShoppingCart, BarChart3, Trophy, Dumbbell, Shield, Code, DollarSign, ExternalLink, Check, X as XIcon, RefreshCw, Upload, Server } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

export default function AdminSettings() {
  const { admin, isSuperAdmin } = useAuth();
  const { labels } = useBusiness();
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
    secondary_color: '',
    bg_color: '',
    menu_color: '',
    text_color: '',
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

  // Redsys TPV config
  const [redsysData, setRedsysData] = useState({ redsys_merchant_code: '', redsys_terminal: '001', redsys_secret_key: '', redsys_environment: 'sandbox' });
  const [redsysStatus, setRedsysStatus] = useState({ enabled: false, has_credentials: false, masked_merchant_code: '', terminal: '', environment: 'sandbox' });
  const [showRedsysKey, setShowRedsysKey] = useState(false);
  const [savingRedsys, setSavingRedsys] = useState(false);

  // Active payment gateway
  const [gatewayInfo, setGatewayInfo] = useState({ active_gateway: 'none', stripe_configured: false, redsys_configured: false, mercadopago_configured: false });
  const [savingGateway, setSavingGateway] = useState(false);

  // Currency
  const [gymCurrency, setGymCurrency] = useState('EUR');
  const [maxDevices, setMaxDevices] = useState(2);
  const [savingDevices, setSavingDevices] = useState(false);

  // Account settings (Super Admin)
  const [accountData, setAccountData] = useState({ email: '', password: '', current_password: '' });
  const [savingAccount, setSavingAccount] = useState(false);
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);

  // SaaS Subscription (for Gym Admins)
  const [subscription, setSubscription] = useState(null);
  const [availablePlans, setAvailablePlans] = useState([]);
  const [subscribing, setSubscribing] = useState(false);
  const [showPlanSelector, setShowPlanSelector] = useState(false);

  useEffect(() => {
    if (admin?.gym_id) {
      fetchGym();
      fetchStripeConfig();
      fetchMpConfig();
      fetchRedsysConfig();
      fetchGatewayInfo();
      fetchSubscription();
    } else {
      setLoading(false);
    }
    if (admin?.email) {
      setAccountData(prev => ({ ...prev, email: admin.email }));
    }
  }, [admin]);

  const fetchSubscription = async () => {
    try {
      const [subRes, plansRes] = await Promise.all([
        getMySubscription(),
        getAvailableSaaSPlans()
      ]);
      setSubscription(subRes.data);
      setAvailablePlans(plansRes.data);
    } catch (e) { console.error('Error fetching subscription:', e); }
  };

  const handleSubscribe = async (planId) => {
    setSubscribing(true);
    try {
      const res = await subscribeSaaSPlan(planId);
      if (res.data.free) {
        toast.success('Plan gratuito activado');
        fetchSubscription();
      } else if (res.data.payment_url) {
        toast.success('Redirigiendo a Stripe...');
        window.open(res.data.payment_url, '_blank');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error al suscribirse');
    } finally {
      setSubscribing(false);
      setShowPlanSelector(false);
    }
  };

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
        secondary_color: response.data.secondary_color || '',
        bg_color: response.data.bg_color || '',
        menu_color: response.data.menu_color || '',
        text_color: response.data.text_color || '',
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

  const fetchRedsysConfig = async () => {
    try {
      const response = await getRedsysConfig(admin.gym_id);
      setRedsysStatus(response.data);
      setRedsysData(prev => ({ ...prev, redsys_terminal: response.data.terminal || '001', redsys_environment: response.data.environment || 'sandbox' }));
    } catch (error) {
      console.error('Error fetching Redsys config:', error);
    }
  };

  const handleSaveRedsys = async () => {
    if (!redsysData.redsys_merchant_code && !redsysStatus.has_credentials) {
      toast.error('Ingresa el codigo de comercio');
      return;
    }
    setSavingRedsys(true);
    try {
      const payload = { redsys_enabled: true, redsys_environment: redsysData.redsys_environment };
      if (redsysData.redsys_merchant_code) payload.redsys_merchant_code = redsysData.redsys_merchant_code;
      if (redsysData.redsys_terminal) payload.redsys_terminal = redsysData.redsys_terminal;
      if (redsysData.redsys_secret_key) payload.redsys_secret_key = redsysData.redsys_secret_key;
      await updateRedsysConfig(admin.gym_id, payload);
      toast.success('Configuracion de Redsys guardada');
      setRedsysData(prev => ({ ...prev, redsys_merchant_code: '', redsys_secret_key: '' }));
      fetchRedsysConfig();
      // Auto-activate Redsys as payment gateway
      try { await setPaymentGateway(admin.gym_id, 'redsys'); fetchGatewayInfo(); } catch {}
    } catch (error) {
      toast.error('Error al guardar Redsys');
    } finally { setSavingRedsys(false); }
  };

  const handleDisableRedsys = async () => {
    try {
      await updateRedsysConfig(admin.gym_id, { redsys_enabled: false });
      toast.success('Redsys deshabilitado');
      fetchRedsysConfig();
    } catch (error) { toast.error('Error'); }
  };

  const fetchGatewayInfo = async () => {
    try {
      const res = await getPaymentGateway(admin.gym_id);
      setGatewayInfo(res.data);
    } catch (error) { console.error('Error fetching gateway:', error); }
  };

  const handleSetGateway = async (gateway) => {
    setSavingGateway(true);
    try {
      await setPaymentGateway(admin.gym_id, gateway);
      toast.success(gateway === 'none' ? 'Pasarela desactivada' : `${gateway.charAt(0).toUpperCase() + gateway.slice(1)} activada`);
      fetchGatewayInfo();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al cambiar pasarela');
    } finally { setSavingGateway(false); }
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
      toast.success('Configuracion guardada');
      document.documentElement.style.setProperty('--gym-primary', formData.primary_color);
      if (formData.bg_color) document.documentElement.style.setProperty('--admin-bg', formData.bg_color);
      if (formData.menu_color) document.documentElement.style.setProperty('--admin-menu', formData.menu_color);
      if (formData.text_color) document.documentElement.style.setProperty('--admin-text', formData.text_color);
      if (formData.secondary_color) document.documentElement.style.setProperty('--gym-secondary', formData.secondary_color);
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
      // Auto-activate Stripe as payment gateway
      if (payload.stripe_secret_key) {
        try { await setPaymentGateway(admin.gym_id, 'stripe'); fetchGatewayInfo(); } catch {}
      }
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
        <p className="text-zinc-400 text-sm">{admin?.gym_id ? `Personaliza tu ${labels.businessName.toLowerCase()} y configura opciones` : 'Administra tu cuenta'}</p>
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
          <p style={{ color: 'var(--text-muted)' }}>No tienes un gimnasio asignado</p>
        </div>
      )}

      {/* Mi Plan SaaS Section - for Gym Admins */}
      {admin?.gym_id && (
        <MiPlanSection 
          subscription={subscription} 
          availablePlans={availablePlans} 
          subscribing={subscribing} 
          showPlanSelector={showPlanSelector}
          setShowPlanSelector={setShowPlanSelector}
          handleSubscribe={handleSubscribe} 
        />
      )}

      {admin?.gym_id && (<>
      {/* Payment Gateway Selector - Solo Super Admin */}
      {(admin?.role === 'super_admin' || admin?.original_role === 'super_admin') && (
      <div className="stat-card border-2 border-zinc-700/50" data-testid="gateway-selector-section">
        <div className="flex items-center gap-2 mb-6">
          <CreditCard size={20} style={{ color: 'var(--gym-primary)' }} />
          <h3 className="font-bold text-lg">Pasarela de Pago Activa</h3>
        </div>
        <p className="text-xs text-zinc-500 mb-4">Selecciona la pasarela que usaran los socios para pagar sus membresias. Solo puede haber una activa a la vez.</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { key: 'none', label: 'Ninguna', color: 'zinc', desc: 'Pagos desactivados' },
            { key: 'redsys', label: 'Redsys', color: 'red', desc: gatewayInfo.redsys_configured ? 'Credenciales OK' : 'Sin configurar' },
            { key: 'stripe', label: 'Stripe', color: 'blue', desc: gatewayInfo.stripe_configured ? 'Credenciales OK' : 'Sin configurar' },
            { key: 'mercadopago', label: 'MercadoPago', color: 'cyan', desc: gatewayInfo.mercadopago_configured ? 'Credenciales OK' : 'Sin configurar' },
          ].map(gw => (
            <button
              key={gw.key}
              onClick={() => handleSetGateway(gw.key)}
              disabled={savingGateway}
              className={`p-4 rounded-xl border-2 text-left transition-all ${
                gatewayInfo.active_gateway === gw.key
                  ? `border-${gw.color}-500 bg-${gw.color}-500/10`
                  : 'border-zinc-700 hover:border-zinc-500'
              }`}
              style={gatewayInfo.active_gateway === gw.key ? { borderColor: gw.key === 'none' ? '#71717a' : gw.key === 'redsys' ? '#ef4444' : gw.key === 'stripe' ? '#3b82f6' : '#06b6d4', background: gw.key === 'none' ? 'rgba(113,113,122,0.1)' : gw.key === 'redsys' ? 'rgba(239,68,68,0.1)' : gw.key === 'stripe' ? 'rgba(59,130,246,0.1)' : 'rgba(6,182,212,0.1)' } : {}}
              data-testid={`gateway-${gw.key}-btn`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-sm">{gw.label}</span>
                {gatewayInfo.active_gateway === gw.key && <CheckCircle size={16} className="text-emerald-400" />}
              </div>
              <p className={`text-[10px] ${gw.key !== 'none' && !gatewayInfo[`${gw.key}_configured`] ? 'text-amber-400' : 'text-zinc-500'}`}>{gw.desc}</p>
            </button>
          ))}
        </div>
      </div>
      )}

      {/* Stripe / Payment Gateway Configuration - Solo Super Admin */}
      {(admin?.role === 'super_admin' || admin?.original_role === 'super_admin') && (
      <div className="stat-card border-2 border-zinc-700/50">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <CreditCard size={20} className="text-blue-400" />
            <h3 className="font-bold text-lg">Pasarela de Pagos (Stripe)</h3>
          </div>
          {stripeStatus.has_stripe_key && (
            <button onClick={async () => {
              if (!window.confirm('Desactivar Stripe para este gimnasio?')) return;
              try {
                await updateStripeConfig(admin.gym_id, { stripe_secret_key: '__REMOVE__', stripe_enabled: false });
                toast.success('Stripe desactivado');
                fetchStripeConfig();
              } catch { toast.error('Error'); }
            }} className="text-xs text-red-400 hover:text-red-300 px-3 py-1 rounded-lg border border-red-500/30 hover:bg-red-500/10 transition-colors" data-testid="stripe-disable-btn">
              Desactivar
            </button>
          )}
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
      )}

      {/* Redsys TPV Virtual Configuration - Solo Super Admin */}
      {(admin?.role === 'super_admin' || admin?.original_role === 'super_admin') && (
      <div className="stat-card border-2 border-zinc-700/50" data-testid="redsys-config-section">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <CreditCard size={20} className="text-red-400" />
            <h3 className="font-bold text-lg">TPV Virtual (Redsys)</h3>
          </div>
          {redsysStatus.enabled && (
            <button onClick={handleDisableRedsys} className="text-xs text-red-400 hover:text-red-300 px-3 py-1 rounded-lg border border-red-500/30 hover:bg-red-500/10 transition-colors" data-testid="redsys-disable-btn">
              Deshabilitar
            </button>
          )}
        </div>

        <div className="flex items-center gap-3 mb-6 p-3 rounded-xl bg-zinc-800/50">
          {redsysStatus.enabled && redsysStatus.has_credentials ? (
            <>
              <CheckCircle size={20} className="text-emerald-500 shrink-0" />
              <div>
                <p className="font-medium text-emerald-400">Redsys Configurado</p>
                <p className="text-xs text-zinc-500">Comercio: {redsysStatus.masked_merchant_code} · Terminal: {redsysStatus.terminal} · {redsysStatus.environment === 'production' ? 'Produccion' : 'Sandbox'}</p>
              </div>
            </>
          ) : (
            <>
              <AlertTriangle size={20} className="text-amber-500 shrink-0" />
              <div>
                <p className="font-medium text-amber-400">Redsys No Configurado</p>
                <p className="text-xs text-zinc-500">Configura las credenciales del TPV virtual de tu banco</p>
              </div>
            </>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-zinc-400 mb-2 block">
              Codigo de Comercio (FUC) {redsysStatus.has_credentials && '(dejar vacio para mantener)'}
            </label>
            <Input
              value={redsysData.redsys_merchant_code}
              onChange={(e) => setRedsysData({ ...redsysData, redsys_merchant_code: e.target.value })}
              placeholder={redsysStatus.has_credentials ? 'Codigo actual guardado' : '999008881'}
              className="input-dark"
              data-testid="redsys-merchant-code-input"
            />
          </div>

          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Terminal</label>
            <Input
              value={redsysData.redsys_terminal}
              onChange={(e) => setRedsysData({ ...redsysData, redsys_terminal: e.target.value })}
              placeholder="001"
              className="input-dark w-[120px]"
              data-testid="redsys-terminal-input"
            />
          </div>

          <div>
            <label className="text-sm text-zinc-400 mb-2 block">
              Clave Secreta (SHA-256) {redsysStatus.has_credentials && '(dejar vacio para mantener)'}
            </label>
            <div className="relative">
              <Input
                type={showRedsysKey ? 'text' : 'password'}
                value={redsysData.redsys_secret_key}
                onChange={(e) => setRedsysData({ ...redsysData, redsys_secret_key: e.target.value })}
                placeholder={redsysStatus.has_credentials ? 'Clave actual guardada' : 'Clave proporcionada por tu banco'}
                className="input-dark pr-10"
                data-testid="redsys-secret-key-input"
              />
              <button type="button" onClick={() => setShowRedsysKey(!showRedsysKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
                {showRedsysKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <p className="text-xs text-zinc-500 mt-1">La clave HMAC SHA-256 que te proporciona tu entidad bancaria</p>
          </div>

          <div>
            <label className="text-sm text-zinc-400 mb-2 block">Entorno</label>
            <Select value={redsysData.redsys_environment} onValueChange={(v) => setRedsysData({ ...redsysData, redsys_environment: v })}>
              <SelectTrigger className="w-[220px] bg-zinc-800 border-zinc-700" data-testid="redsys-environment-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                <SelectItem value="sandbox">Sandbox (Pruebas)</SelectItem>
                <SelectItem value="production">Produccion (Real)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleSaveRedsys} disabled={savingRedsys} className="btn-gym-primary" data-testid="save-redsys-btn">
            <CreditCard size={18} className="mr-2" />
            {savingRedsys ? 'Guardando...' : 'Activar y Guardar Redsys'}
          </Button>
        </div>
      </div>
      )}

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
            <label className="text-sm text-zinc-400 mb-2 block">Logo del Gimnasio</label>
            <div className="flex gap-3 items-center">
              <Input
                value={formData.logo_url}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                placeholder="URL del logo o sube un archivo"
                className="input-dark flex-1"
              />
              <label className="cursor-pointer px-3 py-2 rounded-lg text-sm font-medium transition-colors" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)', border: '1px solid var(--border-primary)' }}>
                Subir
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={async (e) => {
                    const file = e.target.files[0];
                    if (!file) return;
                    const fd = new FormData();
                    fd.append('file', file);
                    try {
                      const res = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/upload/gym-logo/${gym?.id}`, fd, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                      });
                      const logoUrl = res.data.logo_url.startsWith('http') ? res.data.logo_url : `${process.env.REACT_APP_BACKEND_URL}${res.data.logo_url}`;
                      setFormData(prev => ({ ...prev, logo_url: logoUrl }));
                      toast.success('Logo subido correctamente');
                    } catch (err) {
                      toast.error(err.response?.data?.detail || 'Error al subir logo');
                    }
                    e.target.value = '';
                  }}
                />
              </label>
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

        {/* Corporate Colors */}
        <div className="mt-6 pt-6 border-t border-zinc-700">
          <h4 className="font-bold text-sm text-zinc-300 mb-4 flex items-center gap-2"><Palette size={16} /> Colores Corporativos del Panel</h4>
          <p className="text-xs text-zinc-500 mb-4">Personaliza los colores del panel admin para tu marca. Dejar vacio usa los colores por defecto.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Fondo del panel</label>
              <div className="flex items-center gap-2">
                <input type="color" value={formData.bg_color || '#09090B'} onChange={(e) => setFormData({ ...formData, bg_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer border-0" />
                <Input value={formData.bg_color} onChange={(e) => setFormData({ ...formData, bg_color: e.target.value })} className="input-dark flex-1 font-mono text-xs" placeholder="#09090B" data-testid="bg-color-input" />
              </div>
            </div>
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Color del menu lateral</label>
              <div className="flex items-center gap-2">
                <input type="color" value={formData.menu_color || '#111113'} onChange={(e) => setFormData({ ...formData, menu_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer border-0" />
                <Input value={formData.menu_color} onChange={(e) => setFormData({ ...formData, menu_color: e.target.value })} className="input-dark flex-1 font-mono text-xs" placeholder="#111113" data-testid="menu-color-input" />
              </div>
            </div>
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Color del texto</label>
              <div className="flex items-center gap-2">
                <input type="color" value={formData.text_color || '#FAFAFA'} onChange={(e) => setFormData({ ...formData, text_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer border-0" />
                <Input value={formData.text_color} onChange={(e) => setFormData({ ...formData, text_color: e.target.value })} className="input-dark flex-1 font-mono text-xs" placeholder="#FAFAFA" data-testid="text-color-input" />
              </div>
            </div>
            <div>
              <label className="text-xs text-zinc-400 mb-1 block">Color secundario</label>
              <div className="flex items-center gap-2">
                <input type="color" value={formData.secondary_color || '#3B82F6'} onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })} className="w-8 h-8 rounded cursor-pointer border-0" />
                <Input value={formData.secondary_color} onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })} className="input-dark flex-1 font-mono text-xs" placeholder="#3B82F6" data-testid="secondary-color-input" />
              </div>
            </div>
          </div>
          {/* Live Preview */}
          <div className="mt-4 p-3 rounded-xl border border-zinc-700 flex items-center gap-3" style={{ backgroundColor: formData.bg_color || '#09090B' }}>
            <div className="w-10 rounded-lg p-2" style={{ backgroundColor: formData.menu_color || '#111113' }}>
              <div className="w-full h-1.5 rounded mb-1" style={{ backgroundColor: formData.primary_color }} />
              <div className="w-3/4 h-1 rounded mb-1" style={{ backgroundColor: formData.text_color || '#FAFAFA', opacity: 0.3 }} />
              <div className="w-1/2 h-1 rounded" style={{ backgroundColor: formData.text_color || '#FAFAFA', opacity: 0.3 }} />
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold" style={{ color: formData.text_color || '#FAFAFA' }}>Vista previa del panel</p>
              <p className="text-[10px]" style={{ color: formData.secondary_color || '#3B82F6' }}>Texto secundario</p>
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

      {/* Deploy Tools - Super Admin Only */}
      {isSuperAdmin && (
        <DeploySection />
      )}
    </div>
  );
}


const SAAS_FEATURES = [
  { key: 'has_qr_access', label: 'Control de Acceso QR', icon: QrCode },
  { key: 'has_guest_passes', label: 'Pases de Invitados', icon: Users },
  { key: 'has_classes', label: 'Clases y Reservas', icon: Calendar },
  { key: 'has_pos', label: 'TPV / Punto de Venta', icon: ShoppingCart },
  { key: 'has_analytics', label: 'Analytics Avanzado', icon: BarChart3 },
  { key: 'has_gamification', label: 'Gamificacion', icon: Trophy },
  { key: 'has_routines', label: 'Rutinas de Ejercicio', icon: Dumbbell },
  { key: 'has_email_smtp', label: 'Emails Automaticos (SMTP)', icon: Mail },
  { key: 'has_stripe_members', label: 'Pagos Stripe (Socios)', icon: CreditCard },
  { key: 'has_mercadopago', label: 'MercadoPago', icon: DollarSign },
  { key: 'has_iframes', label: 'Iframes Personalizados', icon: Code },
  { key: 'has_advanced_accounting', label: 'Contabilidad Avanzada', icon: Shield },
];

function MiPlanSection({ subscription, availablePlans, subscribing, showPlanSelector, setShowPlanSelector, handleSubscribe }) {
  const plan = subscription?.plan;
  const memberCount = subscription?.member_count || 0;
  const maxMembers = subscription?.max_members || 500;
  const usagePercent = maxMembers > 0 ? Math.min((memberCount / maxMembers) * 100, 100) : 0;

  return (
    <div className="stat-card" style={{ border: '2px solid var(--border-secondary)' }} data-testid="my-saas-plan-section">
      <div className="flex items-center gap-2 mb-6">
        <Crown size={20} style={{ color: 'var(--gym-primary)' }} />
        <h3 className="font-bold text-lg">Mi Plan SaaS</h3>
      </div>

      {plan ? (
        <div className="space-y-5">
          {/* Current plan info */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)' }}>
            <div>
              <h4 className="text-xl font-black mb-1">{plan.name}</h4>
              {plan.description && <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{plan.description}</p>}
            </div>
            <div className="text-right">
              <p className="text-2xl font-black" style={{ color: 'var(--gym-primary)' }}>
                {plan.price_monthly > 0 ? `${plan.price_monthly} ${plan.currency}/mes` : 'Gratis'}
              </p>
            </div>
          </div>

          {/* Capacity bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span style={{ color: 'var(--text-secondary)' }}>Capacidad de socios</span>
              <span className="font-mono font-bold">{memberCount} / {maxMembers.toLocaleString()}</span>
            </div>
            <div className="w-full h-3 rounded-full" style={{ background: 'var(--bg-tertiary)' }}>
              <div className="h-full rounded-full transition-all" style={{
                width: `${usagePercent}%`,
                background: usagePercent > 90 ? '#EF4444' : usagePercent > 70 ? '#F59E0B' : 'var(--gym-primary)'
              }} />
            </div>
            <p className="text-xs mt-1" style={{ color: usagePercent > 90 ? '#EF4444' : 'var(--text-muted)' }}>
              {usagePercent > 90 ? 'Cerca del limite! Considera actualizar tu plan.' : `${usagePercent.toFixed(0)}% utilizado`}
            </p>
          </div>

          {/* Features list */}
          <div>
            <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>Caracteristicas incluidas</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {SAAS_FEATURES.map(f => {
                const included = plan[f.key];
                const Icon = f.icon;
                return (
                  <div key={f.key} className="flex items-center gap-2 p-2 rounded-lg text-sm" style={{ background: 'var(--bg-tertiary)' }}>
                    {included ? <Check size={14} className="text-emerald-500 shrink-0" /> : <XIcon size={14} className="text-red-400 shrink-0" />}
                    <Icon size={14} style={{ color: included ? 'var(--text-secondary)' : 'var(--text-dim)' }} />
                    <span style={{ color: included ? 'var(--text-primary)' : 'var(--text-dim)' }}>{f.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Change plan */}
          <button onClick={() => setShowPlanSelector(!showPlanSelector)} className="text-sm px-4 py-2 rounded-lg transition-colors" style={{ background: 'var(--bg-tertiary)', color: 'var(--gym-primary)', border: '1px solid var(--border-secondary)' }} data-testid="change-plan-btn">
            Cambiar Plan
          </button>
        </div>
      ) : (
        <div className="text-center py-6">
          <AlertTriangle size={40} className="mx-auto mb-3 text-amber-500" />
          <p className="font-bold mb-2">Sin plan asignado</p>
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>Contacta al administrador o elige un plan disponible</p>
          <button onClick={() => setShowPlanSelector(true)} className="btn-gym-primary" data-testid="select-plan-btn">
            <CreditCard size={16} className="inline mr-2" /> Ver Planes Disponibles
          </button>
        </div>
      )}

      {/* Plan selector */}
      {showPlanSelector && availablePlans.length > 0 && (
        <div className="mt-5 p-4 rounded-xl" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)' }} data-testid="plan-selector">
          <h4 className="font-bold mb-3">Planes Disponibles</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {availablePlans.map(p => {
              const isCurrent = subscription?.saas_plan_id === p.id;
              const featureCount = SAAS_FEATURES.filter(f => p[f.key]).length;
              return (
                <div key={p.id} className="p-4 rounded-xl relative transition-colors" style={{
                  background: 'var(--bg-secondary)',
                  border: isCurrent ? '2px solid var(--gym-primary)' : '1px solid var(--border-secondary)'
                }} data-testid={`available-plan-${p.id}`}>
                  {isCurrent && <span className="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full font-bold" style={{ background: 'var(--gym-primary)', color: '#000' }}>ACTUAL</span>}
                  <h5 className="font-bold text-lg">{p.name}</h5>
                  <p className="text-2xl font-black mt-1" style={{ color: 'var(--gym-primary)' }}>
                    {p.price_monthly > 0 ? `${p.price_monthly} ${p.currency}/mes` : 'Gratis'}
                  </p>
                  {p.description && <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{p.description}</p>}
                  <p className="text-xs mt-2" style={{ color: 'var(--text-secondary)' }}>{p.max_members.toLocaleString()} socios | {featureCount} caracteristicas</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {SAAS_FEATURES.filter(f => p[f.key]).map(f => (
                      <span key={f.key} className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>{f.label.split(' ')[0]}</span>
                    ))}
                  </div>
                  {!isCurrent && (
                    <button onClick={() => handleSubscribe(p.id)} disabled={subscribing} className="mt-3 w-full btn-gym-primary text-sm" data-testid={`subscribe-plan-${p.id}`}>
                      {subscribing ? <Loader2 size={14} className="animate-spin inline mr-1" /> : <ExternalLink size={14} className="inline mr-1" />}
                      {p.price_monthly > 0 ? 'Suscribirse con Stripe' : 'Activar Plan Gratis'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          <button onClick={() => setShowPlanSelector(false)} className="mt-3 text-sm" style={{ color: 'var(--text-muted)' }}>Cerrar</button>
        </div>
      )}
    </div>
  );
}


function DeploySection() {
  const [syncing, setSyncing] = useState(false);
  const [restarting, setRestarting] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL;

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await axios.post(`${API_URL}/api/deploy/sync-backend`);
      setLastResult(res.data);
      if (res.data.success) {
        toast.success(`${res.data.synced} archivos sincronizados`);
      } else {
        toast.error(res.data.message);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al sincronizar');
    } finally { setSyncing(false); }
  };

  const handleRestart = async () => {
    if (!window.confirm('Reiniciar el backend? El servicio estara inactivo ~3 segundos.')) return;
    setRestarting(true);
    try {
      await axios.post(`${API_URL}/api/deploy/restart-backend`);
      toast.success('Backend reiniciando... espera 5 segundos y recarga la pagina');
    } catch (err) {
      toast.error('Error al reiniciar');
    } finally {
      setTimeout(() => setRestarting(false), 5000);
    }
  };

  return (
    <div className="mt-8 p-6 rounded-2xl" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }} data-testid="deploy-section">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.1)' }}>
          <Server size={20} className="text-red-500" />
        </div>
        <div>
          <h3 className="font-bold text-lg">Despliegue Backend</h3>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Sincronizar archivos de Plesk y reiniciar servidor</p>
        </div>
      </div>

      <div className="flex gap-3">
        <Button onClick={handleSync} disabled={syncing} variant="outline" className="border-zinc-700" data-testid="sync-backend-btn">
          <Upload size={16} className="mr-2" />
          {syncing ? 'Sincronizando...' : '1. Sincronizar Archivos'}
        </Button>
        <Button onClick={handleRestart} disabled={restarting} variant="outline" className="border-red-800 text-red-400 hover:bg-red-500/10" data-testid="restart-backend-btn">
          <RefreshCw size={16} className={`mr-2 ${restarting ? 'animate-spin' : ''}`} />
          {restarting ? 'Reiniciando...' : '2. Reiniciar Backend'}
        </Button>
      </div>

      {lastResult && lastResult.files && (
        <div className="mt-4 p-3 rounded-lg text-sm" style={{ background: 'var(--bg-tertiary)' }}>
          <p className="font-medium mb-1">{lastResult.synced} archivos sincronizados:</p>
          <div className="flex flex-wrap gap-1">
            {lastResult.files.map(f => (
              <span key={f} className="text-xs px-2 py-0.5 rounded" style={{ background: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>{f}</span>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs mt-4" style={{ color: 'var(--text-dim)' }}>
        Proceso: Sube archivos .py por File Manager de c.ingresoqr.com → Clic "Sincronizar" → Clic "Reiniciar"
      </p>
    </div>
  );
}
