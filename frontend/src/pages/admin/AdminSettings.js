import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getGym, updateGym } from '../../lib/api';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Save, Palette, Clock, Image } from 'lucide-react';
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

  useEffect(() => {
    if (admin?.gym_id) {
      fetchGym();
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

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateGym(admin.gym_id, formData);
      toast.success('Configuración guardada');
      
      // Update preview
      document.documentElement.style.setProperty('--gym-primary', formData.primary_color);
    } catch (error) {
      toast.error('Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const presetColors = [
    '#E1FF01', // Lime
    '#FF6B6B', // Red
    '#4ECDC4', // Teal
    '#45B7D1', // Blue
    '#96CEB4', // Green
    '#FFEAA7', // Yellow
    '#DDA0DD', // Plum
    '#FF8C00', // Orange
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
