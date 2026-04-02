import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import { DollarSign, FileText, Download, Calendar, TrendingUp, CreditCard, Banknote, Zap, Trash2, AlertTriangle, FileBarChart } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { format, subDays, startOfWeek, startOfMonth } from 'date-fns';
import { es } from 'date-fns/locale';
import { createCashWithdrawal, pruneOldRecords, downloadSalesReportPDF } from '../../lib/api';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminAccounting() {
  const { admin, isSuperAdmin } = useAuth();
  const [report, setReport] = useState(null);
  const [allTransactions, setAllTransactions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'));
  const [dateTo, setDateTo] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [quickFilter, setQuickFilter] = useState('30d');
  const [showWithdrawal, setShowWithdrawal] = useState(false);
  const [withdrawalForm, setWithdrawalForm] = useState({ amount: 0, reason: '', notes: '' });

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
      const [reportRes, txRes] = await Promise.all([
        axios.get(`${API}/accounting/report`, { params }),
        axios.get(`${API}/accounting/transactions`, { params })
      ]);
      setReport(reportRes.data);
      setAllTransactions(txRes.data);
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
    const map = { cash: 'Efectivo', card_reception: 'Tarjeta', stripe: 'Stripe', mercadopago: 'MercadoPago' };
    return map[m] || 'Stripe Online';
  };

  const handleWithdrawal = async () => {
    if (!withdrawalForm.amount || withdrawalForm.amount <= 0) { toast.error('Ingresa un monto valido'); return; }
    if (!withdrawalForm.reason) { toast.error('Ingresa un motivo'); return; }
    try {
      const gymId = admin?.gym_id;
      await createCashWithdrawal({ gym_id: gymId, amount: withdrawalForm.amount, reason: withdrawalForm.reason, notes: withdrawalForm.notes });
      toast.success('Retiro registrado');
      setShowWithdrawal(false);
      setWithdrawalForm({ amount: 0, reason: '', notes: '' });
      fetchReport();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const printWithdrawalReceipt = (w) => {
    const win = window.open('', '_blank', 'width=302,height=700');
    win.document.write(`<html><head><style>body{font-family:monospace;width:72mm;margin:0 auto;padding:4mm;}hr{border:0;border-top:1px dashed #000;margin:8px 0}.sig-line{border-bottom:1px solid #000;width:100%;display:inline-block;margin:6px 0}</style></head><body>
      <h3 style="text-align:center;margin:4px 0">RETIRO DE CAJA</h3>
      <p style="text-align:center;font-size:10px">${new Date(w.created_at).toLocaleString()}</p><hr/>
      <p><strong>Monto:</strong> $${w.amount?.toLocaleString()}</p>
      <p><strong>Motivo:</strong> ${w.reason}</p>
      ${w.notes ? `<p><strong>Notas:</strong> ${w.notes}</p>` : ''}
      <p><strong>Registrado por:</strong> ${w.registered_by_name || '-'}</p><hr/>
      <p style="font-size:9px;margin-bottom:12px"><strong>Firma de quien recibe:</strong></p>
      <p><span class="sig-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>
      <p style="font-size:9px"><strong>Nombre:</strong> <span class="sig-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>
      <p style="font-size:9px"><strong>DNI/Pasaporte/NIE:</strong> <span class="sig-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>
      <hr/>
      <p style="font-size:7px;text-align:center;font-style:italic">(Al firmar el recibo, confirmo que recibo conforme la cantidad que aparece en el ticket)</p>
      <p style="text-align:center;font-size:8px;margin-top:8px">Comprobante de retiro</p>
    </body></html>`);
    win.document.close();
    win.print();
  };

  const handlePrune = async () => {
    if (!window.confirm('Esto eliminara registros de acceso anteriores a 6 meses. Esta accion es irreversible. Continuar?')) return;
    try { const r = await pruneOldRecords(6); toast.success(r.data.message); }
    catch (e) { toast.error('Error al purgar registros'); }
  };

  const handleDownloadSalesReport = async (period) => {
    try {
      const gymId = admin?.gym_id;
      const res = await downloadSalesReportPDF(gymId, period, dateFrom, dateTo);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `informe_ventas_${period}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`Informe ${period} descargado`);
    } catch (e) { toast.error('Error al generar PDF'); }
  };

  const PIE_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#06B6D4'];

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
    { name: 'Tarjeta', value: s.card_total || 0 },
    { name: 'Stripe', value: s.stripe_total || 0 },
    { name: 'MercadoPago', value: s.mercadopago_total || 0 },
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

      {/* Sales Reports */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <FileBarChart size={18} className="text-[var(--gym-primary)]" />
          <h3 className="font-bold">Informes de Ventas</h3>
        </div>
        <p className="text-zinc-400 text-sm mb-4">Descarga informes PDF detallados con membresias, ventas POS y retiros.</p>
        <div className="flex flex-wrap gap-2">
          {[
            { period: 'daily', label: 'Diario (hoy)' },
            { period: 'weekly', label: 'Semanal' },
            { period: 'monthly', label: 'Mensual' },
            { period: 'custom', label: 'Periodo personalizado' },
          ].map(r => (
            <button key={r.period} onClick={() => handleDownloadSalesReport(r.period)} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors text-sm" data-testid={`report-${r.period}`}>
              <FileText size={14} /> {r.label}
            </button>
          ))}
        </div>
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
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="stat-card">
          <p className="text-xs text-zinc-500">Total Recaudado</p>
          <p className="text-xl font-black text-[var(--gym-primary)]" data-testid="total-revenue">${s.total_revenue?.toLocaleString() || '0'}</p>
        </div>
        <div className="stat-card">
          <p className="text-xs text-zinc-500">Membresias</p>
          <p className="text-xl font-black">${s.membership_revenue?.toLocaleString() || '0'}</p>
        </div>
        <div className="stat-card">
          <p className="text-xs text-zinc-500">Pendiente de Cobro</p>
          <p className="text-xl font-black text-amber-400" data-testid="total-pending">${allTransactions?.summary?.total_pending?.toLocaleString() || '0'}</p>
          <p className="text-xs text-zinc-500">{allTransactions?.summary?.pending_count || 0} pagos</p>
        </div>
        <div className="stat-card">
          <p className="text-xs text-zinc-500">Efectivo</p>
          <p className="text-xl font-black text-green-400">${s.cash_total?.toLocaleString() || '0'}</p>
        </div>
        <div className="stat-card">
          <p className="text-xs text-zinc-500">Tarjeta+Stripe</p>
          <p className="text-xl font-black text-blue-400">${((s.card_total || 0) + (s.stripe_total || 0)).toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <p className="text-xs text-zinc-500">Retiros</p>
          <p className="text-xl font-black text-red-400">-${s.total_withdrawals?.toLocaleString() || '0'}</p>
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
                <th>Metodo</th>
                <th>Estado</th>
                <th className="text-right">Monto</th>
              </tr>
            </thead>
            <tbody>
              {(report?.transactions || []).length === 0 ? (
                <tr><td colSpan={6} className="text-center text-zinc-500">No hay transacciones</td></tr>
              ) : (
                report.transactions.map((t) => (
                  <tr key={t.id}>
                    <td className="text-sm">{t.created_at?.slice(0, 10)}</td>
                    <td className="font-medium">{t.member_name || '-'}</td>
                    <td>{t.plan_name || '-'}</td>
                    <td>
                      <span className={`badge ${t.payment_method === 'cash' ? 'badge-success' : t.payment_method === 'card_reception' ? 'badge-primary' : t.payment_method === 'mercadopago' ? 'bg-sky-500/10 text-sky-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                        {methodLabel(t.payment_method)}
                      </span>
                    </td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                        t.payment_status === 'paid' 
                          ? 'bg-emerald-500/20 text-emerald-400' 
                          : 'bg-amber-500/20 text-amber-400'
                      }`} data-testid={`tx-status-${t.id}`}>
                        {t.payment_status === 'paid' ? 'Pagado' : 'Pendiente'}
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

      {/* POS Sales */}
      {(report?.pos_sales || []).length > 0 && (
        <div className="stat-card">
          <h3 className="font-bold mb-4">Ventas POS/TPV</h3>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Fecha</th><th>Items</th><th>Metodo</th><th className="text-right">Total</th></tr></thead>
              <tbody>
                {report.pos_sales.map(s => (
                  <tr key={s.id}>
                    <td className="text-sm">{s.created_at?.slice(0, 10)}</td>
                    <td>{(s.items || []).map(i => `${i.product_name}(${i.quantity})`).join(', ')}</td>
                    <td><span className={`badge ${s.payment_method === 'cash' ? 'badge-success' : 'badge-primary'}`}>{s.payment_method === 'cash' ? 'Efectivo' : 'Tarjeta'}</span></td>
                    <td className="text-right font-mono font-bold">${s.total?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cash Withdrawals + Prune */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">Retiros de Caja</h3>
            <button onClick={() => setShowWithdrawal(!showWithdrawal)} className="btn-gym-primary text-sm px-3 py-2" data-testid="withdrawal-btn">+ Retiro</button>
          </div>
          {showWithdrawal && (
            <div className="bg-zinc-800 rounded-xl p-4 mb-4 space-y-3" data-testid="withdrawal-form">
              <input className="input-gym" type="number" placeholder="Monto" value={withdrawalForm.amount} onChange={e => setWithdrawalForm({ ...withdrawalForm, amount: parseFloat(e.target.value) })} />
              <input className="input-gym" placeholder="Motivo" value={withdrawalForm.reason} onChange={e => setWithdrawalForm({ ...withdrawalForm, reason: e.target.value })} />
              <input className="input-gym" placeholder="Notas (opcional)" value={withdrawalForm.notes} onChange={e => setWithdrawalForm({ ...withdrawalForm, notes: e.target.value })} />
              <div className="flex gap-2">
                <button onClick={handleWithdrawal} className="btn-gym-primary text-sm" data-testid="confirm-withdrawal-btn">Registrar Retiro</button>
                <button onClick={() => setShowWithdrawal(false)} className="btn-gym-secondary text-sm">Cancelar</button>
              </div>
            </div>
          )}
          {s.total_withdrawals > 0 && (
            <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-3 mb-3">
              <p className="text-sm text-red-400">Total retirado: <span className="font-bold">${s.total_withdrawals?.toLocaleString()}</span></p>
              <p className="text-sm text-zinc-400">Caja neta: <span className="font-bold text-white">${s.net_cash?.toLocaleString()}</span></p>
            </div>
          )}
          <div className="space-y-2">
            {(report?.withdrawals || []).map(w => (
              <div key={w.id} className="flex items-center justify-between bg-zinc-800/50 rounded-lg p-3">
                <div>
                  <p className="text-sm text-white">{w.reason}</p>
                  <p className="text-xs text-zinc-500">{new Date(w.created_at).toLocaleString()} - {w.registered_by_name}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-red-400 font-bold font-mono">-${w.amount?.toLocaleString()}</span>
                  <button onClick={() => printWithdrawalReceipt(w)} className="text-xs text-[var(--gym-primary)] hover:underline">Ticket</button>
                </div>
              </div>
            ))}
            {(report?.withdrawals || []).length === 0 && <p className="text-zinc-500 text-sm">Sin retiros en este periodo</p>}
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={18} className="text-amber-400" />
            <h3 className="font-bold">Mantenimiento de Datos</h3>
          </div>
          <p className="text-zinc-400 text-sm mb-4">Elimina registros de acceso antiguos para mantener la base de datos optimizada.</p>
          <button onClick={handlePrune} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-900/20 text-red-400 border border-red-800/30 hover:bg-red-900/40 transition-colors" data-testid="prune-btn">
            <Trash2 size={16} />
            Eliminar registros {'>'} 6 meses
          </button>
        </div>
      </div>
    </div>
  );
}
