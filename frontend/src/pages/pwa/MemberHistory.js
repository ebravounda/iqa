import { useState, useEffect } from 'react';
import { getMemberAccessLogs } from '../../lib/api';
import { formatDate, formatTime } from '../../lib/utils';
import { motion } from 'framer-motion';
import { ArrowUpRight, ArrowDownLeft, History } from 'lucide-react';

export default function MemberHistory() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await getMemberAccessLogs();
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching access logs:', error);
    } finally {
      setLoading(false);
    }
  };

  // Group logs by date
  const groupedLogs = logs.reduce((acc, log) => {
    const date = formatDate(log.timestamp);
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(log);
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="member-history">
      <div>
        <h1 className="text-2xl font-black tracking-tight">Historial de Accesos</h1>
        <p className="text-zinc-400 text-sm">{logs.length} registros</p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton h-4 w-24 mb-3" />
              <div className="skeleton h-12 w-full" />
            </div>
          ))}
        </div>
      ) : logs.length === 0 ? (
        <div className="text-center py-16">
          <History size={48} className="mx-auto text-zinc-700 mb-4" />
          <p className="text-zinc-500">No hay accesos registrados</p>
          <p className="text-zinc-600 text-sm">Tu historial aparecerá aquí</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedLogs).map(([date, dayLogs], dateIndex) => (
            <motion.div
              key={date}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: dateIndex * 0.1 }}
            >
              <h3 className="text-sm font-medium text-zinc-500 mb-3 px-1">{date}</h3>
              <div className="stat-card divide-y divide-zinc-800">
                {dayLogs.map((log, index) => (
                  <div 
                    key={log.id} 
                    className="flex items-center justify-between py-4 first:pt-0 last:pb-0"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        log.direction === 'entrada' 
                          ? 'bg-emerald-500/10' 
                          : 'bg-blue-500/10'
                      }`}>
                        {log.direction === 'entrada' ? (
                          <ArrowUpRight size={20} className="text-emerald-500" />
                        ) : (
                          <ArrowDownLeft size={20} className="text-blue-500" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">
                          {log.direction === 'entrada' ? 'Entrada' : 'Salida'}
                        </p>
                        <p className="text-sm text-zinc-500">{log.gym_name || 'Gimnasio'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-sm" style={{ color: 'var(--gym-primary)' }}>
                        {formatTime(log.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
