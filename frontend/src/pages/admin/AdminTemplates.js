import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getGym, updateEmailTemplate } from '../../lib/api';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Button } from '../../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Mail, Save, Info } from 'lucide-react';
import { toast } from 'sonner';

const templateTypes = [
  { type: 'welcome', label: 'Bienvenida', description: 'Se envía cuando se registra un nuevo socio' },
  { type: 'expiring_10', label: 'Vencimiento 10 días', description: 'Se envía 10 días antes de vencer' },
  { type: 'expiring_5', label: 'Vencimiento 5 días', description: 'Se envía 5 días antes de vencer' },
  { type: 'expiring_3', label: 'Vencimiento 3 días', description: 'Se envía 3 días antes de vencer' },
  { type: 'expired', label: 'Membresía Vencida', description: 'Se envía el día que vence' },
  { type: 'payment_success', label: 'Pago Exitoso', description: 'Se envía después de un pago exitoso' },
];

const variables = [
  { name: '{gym_name}', desc: 'Nombre del gimnasio' },
  { name: '{member_name}', desc: 'Nombre del socio' },
  { name: '{member_code}', desc: 'Código del socio' },
  { name: '{member_email}', desc: 'Email del socio' },
  { name: '{expiry_date}', desc: 'Fecha de vencimiento' },
  { name: '{plan_name}', desc: 'Nombre del plan' },
  { name: '{amount}', desc: 'Monto del pago' },
];

export default function AdminTemplates() {
  const { admin } = useAuth();
  const [gym, setGym] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTemplate, setActiveTemplate] = useState('welcome');
  const [templates, setTemplates] = useState({});

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
      
      // Convert array to object
      const templatesObj = {};
      response.data.email_templates?.forEach(t => {
        templatesObj[t.type] = { subject: t.subject, body: t.body };
      });
      setTemplates(templatesObj);
    } catch (error) {
      toast.error('Error al cargar plantillas');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (type) => {
    if (!templates[type]) return;
    
    setSaving(true);
    try {
      await updateEmailTemplate(admin.gym_id, type, templates[type]);
      toast.success('Plantilla guardada');
    } catch (error) {
      toast.error('Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const updateTemplate = (type, field, value) => {
    setTemplates(prev => ({
      ...prev,
      [type]: { ...prev[type], [field]: value }
    }));
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="stat-card">
          <div className="skeleton h-64 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-templates">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Plantillas de Email</h1>
        <p className="text-zinc-400 text-sm">Personaliza los emails que reciben tus socios</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editor */}
        <div className="lg:col-span-2">
          <div className="stat-card">
            <Tabs value={activeTemplate} onValueChange={setActiveTemplate}>
              <TabsList className="bg-zinc-800 p-1 mb-6 flex-wrap h-auto">
                {templateTypes.map((t) => (
                  <TabsTrigger 
                    key={t.type} 
                    value={t.type}
                    className="data-[state=active]:bg-[var(--gym-primary)] data-[state=active]:text-black"
                  >
                    {t.label}
                  </TabsTrigger>
                ))}
              </TabsList>

              {templateTypes.map((t) => (
                <TabsContent key={t.type} value={t.type} className="space-y-4">
                  <div className="flex items-center gap-2 p-3 bg-zinc-800/50 rounded-lg">
                    <Info size={16} className="text-blue-400" />
                    <span className="text-sm text-zinc-400">{t.description}</span>
                  </div>
                  
                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Asunto del Email</label>
                    <Input
                      value={templates[t.type]?.subject || ''}
                      onChange={(e) => updateTemplate(t.type, 'subject', e.target.value)}
                      placeholder="Asunto del email"
                      className="input-dark"
                      data-testid={`template-subject-${t.type}`}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Cuerpo del Mensaje</label>
                    <Textarea
                      value={templates[t.type]?.body || ''}
                      onChange={(e) => updateTemplate(t.type, 'body', e.target.value)}
                      placeholder="Contenido del email..."
                      className="input-dark min-h-[200px] font-mono text-sm"
                      data-testid={`template-body-${t.type}`}
                    />
                  </div>

                  <Button 
                    onClick={() => handleSave(t.type)} 
                    disabled={saving}
                    className="btn-gym-primary"
                    data-testid={`save-template-${t.type}`}
                  >
                    <Save size={18} className="mr-2" />
                    {saving ? 'Guardando...' : 'Guardar Plantilla'}
                  </Button>
                </TabsContent>
              ))}
            </Tabs>
          </div>
        </div>

        {/* Variables Reference */}
        <div className="stat-card h-fit">
          <div className="flex items-center gap-2 mb-4">
            <Mail size={18} className="text-zinc-400" />
            <h3 className="font-bold">Variables Disponibles</h3>
          </div>
          <p className="text-xs text-zinc-500 mb-4">
            Usa estas variables en tus plantillas para personalizar los emails
          </p>
          <div className="space-y-2">
            {variables.map((v) => (
              <div key={v.name} className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-0">
                <code className="text-xs bg-zinc-800 px-2 py-1 rounded text-[var(--gym-primary)]">
                  {v.name}
                </code>
                <span className="text-xs text-zinc-500">{v.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
