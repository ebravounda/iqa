import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import { DollarSign, FileText, Download, Calendar, TrendingUp, CreditCard, Banknote, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { format, subDays, startOfWeek, startOfMonth } from 'date-fns';
import { es } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminAccounting() {
  const { admin, isSuperAdmin } = useAuth();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'));
  const [dateTo, setDateTo] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [quickFilter, setQuickFilter] = useState('30d');

  useEffect(() => { fetchReport(); }, [dateFrom, dateTo]);

  const applyQuickFilter = (filter) => {
    setQuickFilter(filter);
    const today = new Date();
    switch (filter) {
      case '7d': setDateFrom(format(subDays(today, 7), 'yyyy-MM-dd')); break;
      case '30d': setDateFrom(format(subDays(today, 30), 'yyyy-MM-dd')); break;
      case 'week': setDateFrom(format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd')); break;
      case 'month': setDateFrom(format(startOfMonth(today), 'yyyy-MM-dd')); break;
      case 'all': setDateFrom(''); break;
      default: break;
    }
    setDateTo(format(today, 'yyyy-MM-dd'));
  };

  const fetchReport = async () => {
    try {
      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const response = await axios.get(`${API}/accounting/report`, { params });
      setReport(response.data);
    } catch (error) {
      toast.error('Error al cargar informe');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      const response = await axios.get(`${API}/accounting/pdf?${params.toString()}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `contabilidad_${dateFrom || 'all'}_${dateTo || 'all'}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF descargado');
    } catch (error) {
      toast.error('Error al generar PDF');
    }
  };

  const methodLabel = (m) => {
    const map = { cash: 'Efectivo', card_reception: 'Tarjeta Recepción', stripe: 'Stripe Online' };
    return map[m] || 'Stripe Online';
  };

  const PIE_COLORS = ['#10B981', '#3B82F6', '#F59E0B'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const s = report?.summary || {};
  const pieData = [
    { name: 'Efectivo', value: s.cash_total || 0 },
    { name: 'Tarjeta Recepción', value: s.card_total || 0 },
    { name: 'Stripe Online', value: s.stripe_total || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6" data-testid="admin-accounting">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Contabilidad</h1>
          <p className="text-zinc-400 text-sm">Ingresos, pagos y reportes financieros</p>
        </div>
        <Button onClick={downloadPDF} className="btn-gym-primary" data-testid="download-pdf-btn">
          <FileText size={18} className="mr-2" />
          Exportar PDF
        </Button>
      </div>

      {/* Filters */}
      <div className="stat-card">
        <div className="flex flex-wrap items-center gap-3">
          {['7d', 'week', '30d', 'month', 'all'].map((f) => (
            <Button
              key={f}
              variant={quickFilter === f ? 'default' : 'outline'}
              size="sm"
              className={quickFilter === f ? 'btn-gym-primary' : 'border-zinc-700'}
              onClick={() => applyQuickFilter(f)}
              data-testid={`filter-${f}`}
            >
              {{ '7d': '7 días', 'week': 'Esta semana', '30d': '30 días', 'month': 'Este mes', 'all': 'Todo' }[f]}
            </Button>
          ))}
          <div className="flex items-center gap-2 ml-auto">
            <Input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setQuickFilter(''); }} className="input-dark w-40" data-testid="date-from" />
            <span className="text-zinc-500">-</span>
            <Input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setQuickFilter(''); }} className="input-dark w-40" data-testid="date-to" />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <DollarSign size={20} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Total Recaudado</p>
              <p className="text-2xl font-black" data-testid="total-revenue">${s.total_revenue?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <TrendingUp size={20} className="text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Transacciones</p>
              <p className="text-2xl font-black">{s.total_transactions || 0}</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
              <Banknote size={20} className="text-green-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Efectivo</p>
              <p className="text-2xl font-black">${s.cash_total?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-yellow-500/10 flex items-center justify-center">
              <CreditCard size={20} className="text-yellow-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Tarjeta + Stripe</p>
              <p className="text-2xl font-black">${((s.card_total || 0) + (s.stripe_total || 0)).toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="stat-card lg:col-span-2">
          <h3 className="font-bold mb-4">Ingresos por Día</h3>
          <div className="h-64">
            {report?.daily_chart?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={report.daily_chart}>
                  <XAxis dataKey="date" tick={{ fill: '#71717a', fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#18181B', border: '1px solid #27272a', borderRadius: '8px', color: '#fff' }}
                    formatter={(v) => [`$${v.toFixed(2)}`, 'Ingreso']} />
                  <Bar dataKey="amount" fill="var(--gym-primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-zinc-500">Sin datos en este período</div>
            )}
          </div>
        </div>
        
        <div className="stat-card">
          <h3 className="font-bold mb-4">Por Método de Pago</h3>
          <div className="h-64">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#18181B', border: '1px solid #27272a', borderRadius: '8px', color: '#fff' }}
                    formatter={(v) => [`$${v.toFixed(2)}`]} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-zinc-500">Sin datos</div>
            )}
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="stat-card">
        <h3 className="font-bold mb-4">Detalle de Transacciones</h3>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Socio</th>
                <th>Plan</th>
                <th>Método</th>
                <th className="text-right">Monto</th>
              </tr>
            </thead>
            <tbody>
              {(report?.transactions || []).length === 0 ? (
                <tr><td colSpan={5} className="text-center text-zinc-500">No hay transacciones</td></tr>
              ) : (
                report.transactions.map((t) => (
                  <tr key={t.id}>
                    <td className="text-sm">{t.created_at?.slice(0, 10)}</td>
                    <td className="font-medium">{t.member_name || '-'}</td>
                    <td>{t.plan_name || '-'}</td>
                    <td>
                      <span className={`badge ${t.payment_method === 'cash' ? 'badge-success' : t.payment_method === 'card_reception' ? 'badge-primary' : 'bg-yellow-500/10 text-yellow-400'}`}>
                        {methodLabel(t.payment_method)}
                      </span>
                    </td>
                    <td className="text-right font-mono font-bold">${t.amount?.toFixed(2)}</td>
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
