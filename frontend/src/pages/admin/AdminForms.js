import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getCustomForms, createCustomForm, deleteCustomForm, getFormResponses, getGyms } from '../../lib/api';
import { toast } from 'sonner';
import { Plus, Trash2, FileText, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

export default function AdminForms() {
  const { admin, isSuperAdmin } = useAuth();
  const [selectedGym, setSelectedGym] = useState(admin?.gym_id || '');
  const [gymsList, setGymsList] = useState([]);
  const gymId = isSuperAdmin ? selectedGym : admin?.gym_id;
  const [forms, setForms] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedForm, setExpandedForm] = useState(null);
  const [responses, setResponses] = useState({});
  const [formData, setFormData] = useState({
    name: '', description: '', show_on_registration: true,
    fields: [{ label: '', field_type: 'text', required: false, options: [], placeholder: '' }]
  });

  const load = useCallback(async () => {
    try {
      const { data } = await getCustomForms(gymId);
      setForms(data);
    } catch (e) { toast.error('Error al cargar formularios'); }
  }, [gymId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (isSuperAdmin) {
      getGyms().then(res => {
        setGymsList(res.data);
        if (res.data.length > 0 && !selectedGym) setSelectedGym(res.data[0].id);
      }).catch(() => {});
    }
  }, [isSuperAdmin]);

  const addField = () => {
    setFormData({
      ...formData,
      fields: [...formData.fields, { label: '', field_type: 'text', required: false, options: [], placeholder: '' }]
    });
  };

  const updateField = (idx, key, value) => {
    const fields = [...formData.fields];
    fields[idx] = { ...fields[idx], [key]: value };
    setFormData({ ...formData, fields });
  };

  const removeField = (idx) => {
    setFormData({ ...formData, fields: formData.fields.filter((_, i) => i !== idx) });
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.name) { toast.error('Nombre requerido'); return; }
    if (formData.fields.some(f => !f.label)) { toast.error('Todas las preguntas deben tener titulo'); return; }
    try {
      await createCustomForm({ ...formData, gym_id: gymId });
      toast.success('Formulario creado');
      setShowCreate(false);
      setFormData({ name: '', description: '', show_on_registration: true, fields: [{ label: '', field_type: 'text', required: false, options: [], placeholder: '' }] });
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Eliminar formulario?')) return;
    try { await deleteCustomForm(id); toast.success('Eliminado'); load(); }
    catch (e) { toast.error('Error'); }
  };

  const viewResponses = async (formId) => {
    if (expandedForm === formId) { setExpandedForm(null); return; }
    try {
      const { data } = await getFormResponses(formId);
      setResponses({ ...responses, [formId]: data });
      setExpandedForm(formId);
    } catch (e) { toast.error('Error'); }
  };

  const fieldTypes = [
    { value: 'text', label: 'Texto corto' },
    { value: 'textarea', label: 'Texto largo' },
    { value: 'select', label: 'Seleccion' },
    { value: 'checkbox', label: 'Si/No' },
    { value: 'number', label: 'Numero' },
  ];

  return (
    <div className="space-y-6" data-testid="forms-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-black text-white">Formularios</h1>
          <p className="text-zinc-400 text-sm">Crea formularios personalizados para tus socios</p>
        </div>
        <div className="flex items-center gap-3">
          {isSuperAdmin && (
            <Select value={selectedGym} onValueChange={setSelectedGym}>
              <SelectTrigger className="bg-zinc-900 border-zinc-700 min-w-[180px]" data-testid="forms-gym-select">
                <SelectValue placeholder="Gimnasio" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {gymsList.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
              </SelectContent>
            </Select>
          )}
          <button onClick={() => setShowCreate(!showCreate)} className="btn-gym-primary" data-testid="create-form-btn">
            <Plus size={16} className="mr-1 inline" /> Nuevo Formulario
          </button>
        </div>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-4" data-testid="form-builder">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-zinc-400 block mb-1">Nombre del formulario *</label>
              <input className="input-gym" placeholder="Ej: Formulario Salud Compatible" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
            </div>
            <div>
              <label className="text-xs text-zinc-400 block mb-1">Descripcion</label>
              <input className="input-gym" placeholder="Descripcion breve" value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} />
            </div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={formData.show_on_registration} onChange={e => setFormData({ ...formData, show_on_registration: e.target.checked })} className="accent-[var(--gym-primary)]" />
            <span className="text-sm text-zinc-300">Mostrar al registrarse</span>
          </label>

          <div className="border border-zinc-700 rounded-xl p-4 space-y-3">
            <h4 className="text-sm font-semibold text-white">Preguntas</h4>
            {formData.fields.map((field, idx) => (
              <div key={idx} className="bg-zinc-800 rounded-lg p-3 grid grid-cols-1 md:grid-cols-4 gap-2 items-end">
                <div className="md:col-span-2">
                  <label className="text-xs text-zinc-400">Pregunta *</label>
                  <input className="input-gym text-sm" placeholder="Ej: Enfermedades base" value={field.label} onChange={e => updateField(idx, 'label', e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Tipo</label>
                  <select className="input-gym text-sm" value={field.field_type} onChange={e => updateField(idx, 'field_type', e.target.value)}>
                    {fieldTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-1 text-xs text-zinc-400 cursor-pointer">
                    <input type="checkbox" checked={field.required} onChange={e => updateField(idx, 'required', e.target.checked)} className="accent-[var(--gym-primary)]" />
                    Obligatorio
                  </label>
                  {formData.fields.length > 1 && (
                    <button type="button" onClick={() => removeField(idx)} className="text-red-400 hover:text-red-300"><Trash2 size={14} /></button>
                  )}
                </div>
                {field.field_type === 'select' && (
                  <div className="md:col-span-4">
                    <label className="text-xs text-zinc-400">Opciones (separadas por coma)</label>
                    <input className="input-gym text-sm" placeholder="Opcion 1, Opcion 2, Opcion 3" value={(field.options || []).join(', ')} onChange={e => updateField(idx, 'options', e.target.value.split(',').map(o => o.trim()).filter(Boolean))} />
                  </div>
                )}
              </div>
            ))}
            <button type="button" onClick={addField} className="text-sm text-[var(--gym-primary)] hover:underline">+ Agregar pregunta</button>
          </div>

          <div className="flex gap-3">
            <button type="submit" className="btn-gym-primary" data-testid="save-form-btn">Crear Formulario</button>
            <button type="button" onClick={() => setShowCreate(false)} className="btn-gym-secondary">Cancelar</button>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {forms.map(form => (
          <div key={form.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5" data-testid={`form-${form.id}`}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-white">{form.name}</h3>
                {form.description && <p className="text-zinc-400 text-sm">{form.description}</p>}
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs text-zinc-500">{form.fields?.length || 0} preguntas</span>
                  {form.show_on_registration && <span className="text-xs bg-[var(--gym-primary)]/10 text-[var(--gym-primary)] px-2 py-0.5 rounded">Visible al registrarse</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => viewResponses(form.id)} className="text-sm px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 flex items-center gap-1" data-testid={`view-responses-${form.id}`}>
                  <Eye size={14} /> Respuestas {expandedForm === form.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                <button onClick={() => handleDelete(form.id)} className="text-sm px-3 py-1.5 rounded-lg bg-red-900/20 text-red-400 hover:bg-red-900/40">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            {expandedForm === form.id && (
              <div className="mt-4 border-t border-zinc-800 pt-4">
                <div className="mb-3">
                  <h4 className="text-sm font-semibold text-zinc-300 mb-2">Campos:</h4>
                  <div className="flex flex-wrap gap-2">
                    {(form.fields || []).map((f, i) => (
                      <span key={i} className="text-xs bg-zinc-800 px-2 py-1 rounded text-zinc-300">{f.label} ({f.field_type}){f.required ? ' *' : ''}</span>
                    ))}
                  </div>
                </div>
                <h4 className="text-sm font-semibold text-zinc-300 mb-2">Respuestas ({(responses[form.id] || []).length}):</h4>
                {(responses[form.id] || []).length === 0 ? (
                  <p className="text-zinc-500 text-sm">Sin respuestas</p>
                ) : (
                  <div className="overflow-x-auto max-h-60 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="border-b border-zinc-700">
                        <th className="text-left p-2 text-zinc-400">Socio</th>
                        <th className="text-left p-2 text-zinc-400">Fecha</th>
                        {(form.fields || []).map((f, i) => <th key={i} className="text-left p-2 text-zinc-400">{f.label}</th>)}
                      </tr></thead>
                      <tbody>
                        {(responses[form.id] || []).map(r => (
                          <tr key={r.id} className="border-b border-zinc-800/50">
                            <td className="p-2 text-white">{r.member?.name || '-'}</td>
                            <td className="p-2 text-zinc-400">{r.created_at?.slice(0, 10)}</td>
                            {(form.fields || []).map((f, i) => (
                              <td key={i} className="p-2 text-zinc-300">{r.responses?.[f.label] || '-'}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {forms.length === 0 && !showCreate && <p className="text-zinc-500 text-center py-8">No hay formularios. Crea el primero para personalizar el registro de tus socios.</p>}
      </div>
    </div>
  );
}
