import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getAccessLogs, getMembers, getMemberAccessStats } from '../../lib/api';
import { formatDateTime } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Calendar } from '../../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../../components/ui/popover';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Search, Calendar as CalendarIcon, Download, ArrowUpRight, ArrowDownLeft, BarChart3, User, FileSpreadsheet } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';

export default function AdminAccess() {
  const { admin, isSuperAdmin } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [memberStats, setMemberStats] = useState(null);
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [loadingStats, setLoadingStats] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, [dateFrom, dateTo]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const gymId = isSuperAdmin ? null : admin?.gym_id;
      const from = dateFrom ? format(dateFrom, 'yyyy-MM-dd') : null;
      const to = dateTo ? format(dateTo, 'yyyy-MM-dd') : null;
      const response = await getAccessLogs(gymId, null, from, to, 500);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching access logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewMemberStats = async (memberId) => {
    setLoadingStats(true);
    setShowMemberModal(true);
    try {
      const response = await getMemberAccessStats(memberId, 30);
      setMemberStats(response.data);
    } catch (error) {
      console.error('Error fetching member stats:', error);
    } finally {
      setLoadingStats(false);
    }
  };

  const filteredLogs = logs.filter(log =>
    log.member_name?.toLowerCase().includes(search.toLowerCase()) ||
    log.member_code?.toLowerCase().includes(search.toLowerCase()) ||
    log.guest_name?.toLowerCase().includes(search.toLowerCase()) ||
    log.guest_code?.toLowerCase().includes(search.toLowerCase())
  );

  // Get unique members from logs for quick summary
  const uniqueMembers = {};
  filteredLogs.forEach(log => {
    const key = log.member_id || log.guest_id;
    if (key && !uniqueMembers[key]) {
      uniqueMembers[key] = {
        id: log.member_id,
        name: log.member_name || log.guest_name,
        code: log.member_code || log.guest_code,
        isGuest: log.is_guest,
        count: 0
      };
    }
    if (key) uniqueMembers[key].count++;
  });

  const exportToExcel = () => {
    const sortedLogs = [...filteredLogs].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );
    const data = sortedLogs.map(log => ({
      'Fecha/Hora': formatDateTime(log.timestamp),
      'Socio': log.member_name || log.guest_name || '-',
      'Código': log.member_code || log.guest_code || '-',
      'Dirección': log.direction === 'entrada' ? 'Entrada' : 'Salida',
      'Tipo': log.is_guest ? 'Invitado' : 'Socio',
      'Válido': log.valid ? 'Sí' : 'No'
    }));
    
    const ws = XLSX.utils.json_to_sheet(data);
    const colWidths = Object.keys(data[0] || {}).map(key => ({
      wch: Math.max(key.length, ...data.map(r => String(r[key] || '').length)) + 2
    }));
    ws['!cols'] = colWidths;
    
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Accesos');
    XLSX.writeFile(wb, `accesos_${format(new Date(), 'yyyy-MM-dd')}.xlsx`);
    toast.success('Archivo Excel descargado');
  };

  return (
    <div className="space-y-6" data-testid="admin-access">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Historial de Accesos</h1>
          <p className="text-zinc-400 text-sm">{logs.length} registros</p>
        </div>
        
        <Button onClick={exportToExcel} variant="outline" className="border-zinc-700" data-testid="export-excel-btn">
          <FileSpreadsheet size={18} className="mr-2" />
          Exportar Excel
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card" data-testid="stat-total-logs">
          <p className="text-zinc-500 text-xs mb-1">Total Registros</p>
          <p className="text-2xl font-black">{filteredLogs.length}</p>
        </div>
        <div className="stat-card" data-testid="stat-entries">
          <p className="text-zinc-500 text-xs mb-1">Entradas</p>
          <p className="text-2xl font-black text-emerald-500">
            {filteredLogs.filter(l => l.direction === 'entrada').length}
          </p>
        </div>
        <div className="stat-card" data-testid="stat-exits">
          <p className="text-zinc-500 text-xs mb-1">Salidas</p>
          <p className="text-2xl font-black text-blue-500">
            {filteredLogs.filter(l => l.direction === 'salida').length}
          </p>
        </div>
        <div className="stat-card" data-testid="stat-unique-members">
          <p className="text-zinc-500 text-xs mb-1">Socios Únicos</p>
          <p className="text-2xl font-black">{Object.keys(uniqueMembers).length}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nombre o código..."
            className="input-dark pl-10"
            data-testid="search-access"
          />
        </div>

        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" className="border-zinc-700 justify-start" data-testid="date-from-btn">
              <CalendarIcon size={18} className="mr-2" />
              {dateFrom ? format(dateFrom, 'dd/MM/yyyy') : 'Desde'}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0 bg-zinc-900 border-zinc-700" align="start">
            <Calendar mode="single" selected={dateFrom} onSelect={setDateFrom} locale={es} />
          </PopoverContent>
        </Popover>

        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" className="border-zinc-700 justify-start" data-testid="date-to-btn">
              <CalendarIcon size={18} className="mr-2" />
              {dateTo ? format(dateTo, 'dd/MM/yyyy') : 'Hasta'}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0 bg-zinc-900 border-zinc-700" align="start">
            <Calendar mode="single" selected={dateTo} onSelect={setDateTo} locale={es} />
          </PopoverContent>
        </Popover>

        {(dateFrom || dateTo) && (
          <Button 
            variant="ghost" 
            onClick={() => { setDateFrom(null); setDateTo(null); }}
            className="text-zinc-400"
          >
            Limpiar
          </Button>
        )}
      </div>

      {/* Table */}
      <div className="stat-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha/Hora</th>
                <th>Socio</th>
                <th>Código</th>
                <th>Dirección</th>
                <th>Tipo</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8">
                    <div className="skeleton h-4 w-32 mx-auto" />
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-zinc-500 py-8">
                    No se encontraron registros
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-zinc-400 text-sm">{formatDateTime(log.timestamp)}</td>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center font-bold text-xs">
                          {(log.member_name || log.guest_name || '?').charAt(0)}
                        </div>
                        <span className="font-medium">{log.member_name || log.guest_name || '-'}</span>
                      </div>
                    </td>
                    <td>
                      <code className="text-sm bg-zinc-800 px-2 py-1 rounded font-mono">
                        {log.member_code || log.guest_code || '-'}
                      </code>
                    </td>
                    <td>
                      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                        log.direction === 'entrada' 
                          ? 'bg-emerald-500/10 text-emerald-500' 
                          : 'bg-blue-500/10 text-blue-500'
                      }`}>
                        {log.direction === 'entrada' ? <ArrowUpRight size={14} /> : <ArrowDownLeft size={14} />}
                        {log.direction === 'entrada' ? 'Entrada' : 'Salida'}
                      </div>
                    </td>
                    <td>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        log.is_guest ? 'bg-purple-500/10 text-purple-400' : 'bg-zinc-800 text-zinc-400'
                      }`}>
                        {log.is_guest ? 'Invitado' : 'Socio'}
                      </span>
                    </td>
                    <td>
                      {log.member_id && !log.is_guest && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewMemberStats(log.member_id)}
                          className="h-8 px-2 text-zinc-400 hover:text-white"
                          data-testid={`view-stats-${log.member_id}`}
                        >
                          <BarChart3 size={16} className="mr-1" />
                          <span className="text-xs">Asistencia</span>
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Member Stats Modal */}
      <Dialog open={showMemberModal} onOpenChange={setShowMemberModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <User size={20} />
              Asistencia del Socio
            </DialogTitle>
          </DialogHeader>
          
          {loadingStats ? (
            <div className="py-8 text-center">
              <div className="skeleton h-4 w-32 mx-auto mb-4" />
              <div className="skeleton h-40 w-full" />
            </div>
          ) : memberStats ? (
            <div className="space-y-6 mt-4">
              {/* Member Info */}
              <div className="flex items-center gap-4 p-4 bg-zinc-800/50 rounded-xl">
                <div className="w-12 h-12 rounded-full bg-zinc-700 flex items-center justify-center font-bold text-lg">
                  {memberStats.member?.name?.charAt(0)}
                </div>
                <div>
                  <p className="font-bold text-lg">{memberStats.member?.name}</p>
                  <p className="text-zinc-500 text-sm font-mono">{memberStats.member?.code}</p>
                </div>
              </div>

              {/* Stats Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-zinc-800/50 rounded-xl" data-testid="member-total-entries">
                  <p className="text-2xl font-black" style={{ color: 'var(--gym-primary)' }}>
                    {memberStats.total_entries}
                  </p>
                  <p className="text-xs text-zinc-500">Entradas Totales</p>
                </div>
                <div className="text-center p-3 bg-zinc-800/50 rounded-xl" data-testid="member-days-attended">
                  <p className="text-2xl font-black text-blue-400">
                    {memberStats.days_attended}
                  </p>
                  <p className="text-xs text-zinc-500">Días Asistidos</p>
                </div>
                <div className="text-center p-3 bg-zinc-800/50 rounded-xl" data-testid="member-attendance-rate">
                  <p className="text-2xl font-black text-emerald-400">
                    {memberStats.attendance_rate}%
                  </p>
                  <p className="text-xs text-zinc-500">Tasa de Asistencia</p>
                </div>
              </div>

              {/* Attendance Chart */}
              {memberStats.daily_breakdown?.length > 0 && (
                <div>
                  <h4 className="font-bold mb-3">Asistencia Diaria (Últimos 30 días)</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={memberStats.daily_breakdown}>
                      <XAxis 
                        dataKey="date" 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fill: '#71717A', fontSize: 10 }}
                        tickFormatter={(v) => v.slice(5)}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fill: '#71717A', fontSize: 10 }}
                        allowDecimals={false}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#18181B', 
                          border: '1px solid #27272A',
                          borderRadius: '8px'
                        }}
                      />
                      <Bar dataKey="entradas" fill="var(--gym-primary)" radius={[2, 2, 0, 0]} name="Entradas" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Recent Logs */}
              {memberStats.recent_logs?.length > 0 && (
                <div>
                  <h4 className="font-bold mb-3">Últimos Accesos</h4>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {memberStats.recent_logs.map((log, i) => (
                      <div key={i} className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
                        <span className="text-sm text-zinc-400">{formatDateTime(log.timestamp)}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          log.direction === 'entrada' 
                            ? 'bg-emerald-500/10 text-emerald-500' 
                            : 'bg-blue-500/10 text-blue-500'
                        }`}>
                          {log.direction === 'entrada' ? 'Entrada' : 'Salida'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-zinc-500 py-8">No hay datos disponibles</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
