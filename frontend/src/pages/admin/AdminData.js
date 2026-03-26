import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { exportMembersExcel, getMembers, getGyms } from '../../lib/api';
import { toast } from 'sonner';
import { Download, Database, Users, FileSpreadsheet } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

export default function AdminData() {
  const { admin, isSuperAdmin } = useAuth();
  const [gyms, setGyms] = useState([]);
  const [selectedGym, setSelectedGym] = useState(admin?.gym_id || '');
  const [memberCount, setMemberCount] = useState(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (isSuperAdmin) {
      getGyms().then(res => {
        setGyms(res.data);
        if (res.data.length > 0 && !selectedGym) setSelectedGym(res.data[0].id);
      }).catch(() => {});
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    const gymId = isSuperAdmin ? selectedGym : admin?.gym_id;
    if (gymId || isSuperAdmin) {
      getMembers(gymId).then(res => setMemberCount(res.data.length)).catch(() => setMemberCount(0));
    }
  }, [selectedGym, admin, isSuperAdmin]);

  const handleExport = async () => {
    setDownloading(true);
    try {
      const gymId = isSuperAdmin ? selectedGym : admin?.gym_id;
      const response = await exportMembersExcel(gymId);
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const disposition = response.headers['content-disposition'];
      const filename = disposition ? disposition.split('filename=')[1] : 'socios.xlsx';
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Excel descargado correctamente');
    } catch (error) {
      toast.error('Error al descargar el archivo');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-data-page">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Datos</h1>
        <p className="text-zinc-400 text-sm">Descarga y exporta la base de datos de socios</p>
      </div>

      {isSuperAdmin && (
        <div className="max-w-sm">
          <label className="text-sm text-zinc-400 mb-1 block">Seleccionar Gimnasio</label>
          <Select value={selectedGym} onValueChange={setSelectedGym}>
            <SelectTrigger className="bg-zinc-900 border-zinc-700" data-testid="data-gym-select">
              <SelectValue placeholder="Seleccionar gimnasio" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-700">
              {gyms.map(g => (
                <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <FileSpreadsheet size={24} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="font-bold text-white text-lg">Base de Datos de Socios</h3>
              <p className="text-zinc-400 text-sm">Exportar a Excel (.xlsx)</p>
            </div>
          </div>
          
          <div className="bg-zinc-800/50 rounded-lg p-4 mb-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-400 flex items-center gap-2"><Users size={14} /> Total de socios</span>
              <span className="text-white font-bold">{memberCount !== null ? memberCount : '...'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-400 flex items-center gap-2"><Database size={14} /> Campos incluidos</span>
              <span className="text-zinc-300">Nombre, Codigo, Telefono, Email, Estado, Fecha</span>
            </div>
          </div>
          
          <p className="text-xs text-zinc-500 mb-4">El archivo se descarga ordenado alfabeticamente por nombre.</p>
          
          <Button 
            onClick={handleExport} 
            disabled={downloading || (isSuperAdmin && !selectedGym)}
            className="w-full btn-gym-primary"
            data-testid="export-excel-btn"
          >
            {downloading ? (
              <><div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" /> Generando...</>
            ) : (
              <><Download size={18} className="mr-2" /> Descargar Excel</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
