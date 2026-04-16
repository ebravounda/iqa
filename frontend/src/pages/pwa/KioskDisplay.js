import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Users, ArrowDownLeft, ArrowUpRight, Activity, ShieldCheck, ShieldX } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function KioskDisplay() {
  const { gymId } = useParams();
  const [data, setData] = useState(null);
  const [activeEvent, setActiveEvent] = useState(null);
  const prevEventsRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/access/display/${gymId}`);
        const newData = res.data;

        // Detect new event (approved or denied)
        if (newData.recent_events && newData.recent_events.length > 0) {
          const newestEvent = newData.recent_events[0];
          const prevEvents = prevEventsRef.current;
          if (!prevEvents || prevEvents.length === 0 || prevEvents[0].id !== newestEvent.id) {
            setActiveEvent(newestEvent);
            setTimeout(() => setActiveEvent(null), 4000);
          }
          prevEventsRef.current = newData.recent_events;
        }

        setData(newData);
        if (newData.primary_color) {
          document.documentElement.style.setProperty('--gym-primary', newData.primary_color);
        }
      } catch (error) {
        console.error('Display fetch error:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [gymId]);

  if (!data) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const logoUrl = data.logo_url
    ? (data.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${data.logo_url}` : data.logo_url)
    : null;

  const now = new Date();
  const timeStr = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  const dateStr = now.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative" data-testid="kiosk-display">
      
      {/* Event overlay */}
      {activeEvent && (
        <div 
          className="absolute inset-0 z-50 flex items-center justify-center"
          style={{
            background: activeEvent.approved 
              ? 'radial-gradient(ellipse at center, rgba(16,185,129,0.25) 0%, rgba(0,0,0,0.95) 70%)'
              : 'radial-gradient(ellipse at center, rgba(239,68,68,0.25) 0%, rgba(0,0,0,0.95) 70%)'
          }}
        >
          <div className="text-center">
            <div className={`w-36 h-36 rounded-full mx-auto mb-8 flex items-center justify-center ${
              activeEvent.approved 
                ? 'bg-emerald-500/20 border-2 border-emerald-500/50' 
                : 'bg-red-500/20 border-2 border-red-500/50'
            }`}>
              {activeEvent.approved ? (
                <span className="text-5xl font-black text-emerald-400">{activeEvent.initials}</span>
              ) : (
                <ShieldX size={64} className="text-red-400" />
              )}
            </div>
            <p className={`text-4xl font-black mb-3 ${
              activeEvent.approved ? 'text-emerald-400' : 'text-red-400'
            }`}>
              {activeEvent.approved ? 'Acceso Aprobado' : 'Acceso Denegado'}
            </p>
            {activeEvent.approved && (
              <p className="text-2xl text-zinc-300 font-medium">{activeEvent.initials}</p>
            )}
            {!activeEvent.approved && activeEvent.reason && (
              <p className="text-xl text-red-300/80">{activeEvent.reason}</p>
            )}
            {activeEvent.approved && (
              <p className="text-lg text-zinc-500 mt-2">
                {activeEvent.direction === 'entrada' ? 'Bienvenido/a' : 'Hasta pronto'}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 border-b border-zinc-800/50">
        <div className="flex items-center gap-4">
          {logoUrl ? (
            <img src={logoUrl} alt={data.gym_name} className="h-12 max-w-[160px] object-contain" />
          ) : (
            <div className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-xl"
              style={{ backgroundColor: 'var(--gym-primary)', color: '#000' }}>
              {data.gym_name?.charAt(0)}
            </div>
          )}
          <h1 className="text-2xl font-bold">{data.gym_name}</h1>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold tabular-nums">{timeStr}</p>
          <p className="text-sm text-zinc-500 capitalize">{dateStr}</p>
        </div>
      </div>

      {/* Main content */}
      <div className="flex h-[calc(100vh-88px)]">
        
        {/* Left: Occupancy */}
        <div className="flex-1 flex flex-col items-center justify-center border-r border-zinc-800/50 px-8">
          <div className="flex items-center gap-3 mb-4">
            <Activity size={24} className="text-zinc-500" />
            <span className="text-lg text-zinc-500 uppercase tracking-widest font-medium">Socios en el interior</span>
          </div>
          
          <div className="relative">
            <p className="text-[12rem] font-black leading-none tabular-nums" style={{ color: 'var(--gym-primary)' }} data-testid="occupancy-count">
              {data.current_occupancy}
            </p>
            {data.max_capacity && (
              <p className="text-center text-zinc-600 text-2xl mt-2">
                de {data.max_capacity} max.
              </p>
            )}
          </div>

          {/* Stats row */}
          <div className="flex gap-12 mt-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <ArrowDownLeft size={20} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{data.entries_today}</p>
                <p className="text-xs text-zinc-500 uppercase">Entradas hoy</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                <ArrowUpRight size={20} className="text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{data.exits_today}</p>
                <p className="text-xs text-zinc-500 uppercase">Salidas hoy</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Recent access */}
        <div className="w-[400px] flex flex-col">
          <div className="px-6 py-4 border-b border-zinc-800/50">
            <p className="text-sm text-zinc-500 uppercase tracking-widest font-medium">Ultimos accesos</p>
          </div>
          <div className="flex-1 overflow-hidden">
            {data.recent_access.map((log, i) => {
              const logTime = new Date(log.timestamp);
              const isEntry = log.direction === 'entrada';
              return (
                <div
                  key={`${log.timestamp}-${i}`}
                  className={`flex items-center gap-4 px-6 py-3.5 border-b border-zinc-800/30 ${
                    i === 0 ? 'bg-zinc-900/50' : ''
                  }`}
                  data-testid={`access-log-${i}`}
                >
                  <div className={`w-11 h-11 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
                    isEntry ? 'bg-emerald-500/20 text-emerald-400' : 'bg-orange-500/20 text-orange-400'
                  }`}>
                    {log.initials}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {isEntry ? (
                        <ArrowDownLeft size={14} className="text-emerald-400 shrink-0" />
                      ) : (
                        <ArrowUpRight size={14} className="text-orange-400 shrink-0" />
                      )}
                      <span className={`text-sm font-medium ${isEntry ? 'text-emerald-400' : 'text-orange-400'}`}>
                        {isEntry ? 'Entrada' : 'Salida'}
                      </span>
                      {log.is_guest && (
                        <span className="text-[10px] bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">Invitado</span>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-zinc-600 tabular-nums shrink-0">
                    {logTime.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              );
            })}
            {data.recent_access.length === 0 && (
              <div className="flex items-center justify-center h-full text-zinc-700">
                <p>Sin accesos hoy</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
