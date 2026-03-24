import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getAccessLogs } from '../../lib/api';
import { formatDateTime, formatDate } from '../../lib/utils';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Calendar } from '../../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../../components/ui/popover';
import { Search, Calendar as CalendarIcon, Download, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export default function AdminAccess() {
  const { admin, isSuperAdmin } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);

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

  const filteredLogs = logs.filter(log =>
    log.member_name?.toLowerCase().includes(search.toLowerCase()) ||
    log.member_code?.toLowerCase().includes(search.toLowerCase())
  );

  const exportToCSV = () => {
    const headers = ['Fecha/Hora', 'Socio', 'Código', 'Dirección'];
    const rows = filteredLogs.map(log => [
      formatDateTime(log.timestamp),
      log.member_name,
      log.member_code,
      log.direction
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `accesos_${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6" data-testid="admin-access">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Historial de Accesos</h1>
          <p className="text-zinc-400 text-sm">{logs.length} registros</p>
        </div>
        
        <Button onClick={exportToCSV} variant="outline" className="border-zinc-700" data-testid="export-csv-btn">
          <Download size={18} className="mr-2" />
          Exportar CSV
        </Button>
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
            <Calendar
              mode="single"
              selected={dateFrom}
              onSelect={setDateFrom}
              locale={es}
            />
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
            <Calendar
              mode="single"
              selected={dateTo}
              onSelect={setDateTo}
              locale={es}
            />
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
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center py-8">
                    <div className="skeleton h-4 w-32 mx-auto" />
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center text-zinc-500 py-8">
                    No se encontraron registros
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-zinc-400">{formatDateTime(log.timestamp)}</td>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center font-bold text-xs">
                          {log.member_name?.charAt(0)}
                        </div>
                        <span className="font-medium">{log.member_name}</span>
                      </div>
                    </td>
                    <td>
                      <code className="text-sm bg-zinc-800 px-2 py-1 rounded font-mono">
                        {log.member_code}
                      </code>
                    </td>
                    <td>
                      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                        log.direction === 'entrada' 
                          ? 'bg-emerald-500/10 text-emerald-500' 
                          : 'bg-blue-500/10 text-blue-500'
                      }`}>
                        {log.direction === 'entrada' ? (
                          <ArrowUpRight size={14} />
                        ) : (
                          <ArrowDownLeft size={14} />
                        )}
                        {log.direction === 'entrada' ? 'Entrada' : 'Salida'}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
