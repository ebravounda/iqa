import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';

export default function AdminIframes() {
  const { admin } = useAuth();
  const gymId = admin?.gym_id;
  const [copied, setCopied] = useState('');

  if (!gymId) return (
    <div className="p-6 text-zinc-400">Selecciona un gimnasio o accede como admin de gym para ver los iframes.</div>
  );

  const baseUrl = window.location.origin;

  const iframes = [
    {
      id: 'register',
      title: 'Registro Publico',
      description: 'Permite que nuevos socios se registren directamente desde tu pagina web.',
      url: `${baseUrl}/register/${gymId}`,
      code: `<iframe src="${baseUrl}/register/${gymId}" width="100%" height="700" style="border:none;border-radius:16px;" title="Registro de Socios"></iframe>`,
    },
    {
      id: 'kiosk',
      title: 'Kiosco de Registro',
      description: 'Modo kiosco completo para tablet o pantalla en recepcion.',
      url: `${baseUrl}/kiosk/${gymId}`,
      code: `<iframe src="${baseUrl}/kiosk/${gymId}" width="100%" height="800" style="border:none;border-radius:16px;" title="Kiosco"></iframe>`,
    },
  ];

  const copy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    toast.success('Copiado al portapapeles');
    setTimeout(() => setCopied(''), 2000);
  };

  return (
    <div className="space-y-6" data-testid="iframes-page">
      <div>
        <h1 className="text-2xl font-black text-white">Iframes</h1>
        <p className="text-zinc-400 text-sm">Integra formularios de tu gimnasio en cualquier pagina web</p>
      </div>

      <div className="space-y-4">
        {iframes.map(iframe => (
          <div key={iframe.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6" data-testid={`iframe-${iframe.id}`}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-bold text-white">{iframe.title}</h3>
                <p className="text-zinc-400 text-sm">{iframe.description}</p>
              </div>
              <a href={iframe.url} target="_blank" rel="noopener noreferrer" className="text-xs text-[var(--gym-primary)] hover:underline">
                Abrir en nueva ventana
              </a>
            </div>

            <div className="mb-4">
              <label className="text-zinc-400 text-xs block mb-1">URL directa:</label>
              <div className="flex items-center gap-2">
                <input className="input-gym flex-1 text-xs font-mono" value={iframe.url} readOnly />
                <button onClick={() => copy(iframe.url, `url-${iframe.id}`)} className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${copied === `url-${iframe.id}` ? 'bg-green-900/30 text-green-400' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'}`} data-testid={`copy-url-${iframe.id}`}>
                  {copied === `url-${iframe.id}` ? 'Copiado' : 'Copiar'}
                </button>
              </div>
            </div>

            <div>
              <label className="text-zinc-400 text-xs block mb-1">Codigo iframe (pegar en tu web):</label>
              <div className="bg-zinc-950 rounded-lg p-3 mb-2">
                <code className="text-xs text-green-400 font-mono break-all">{iframe.code}</code>
              </div>
              <button onClick={() => copy(iframe.code, `code-${iframe.id}`)} className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${copied === `code-${iframe.id}` ? 'bg-green-900/30 text-green-400' : 'bg-[var(--gym-primary)] text-black hover:opacity-80'}`} data-testid={`copy-code-${iframe.id}`}>
                {copied === `code-${iframe.id}` ? 'Copiado!' : 'Copiar codigo iframe'}
              </button>
            </div>

            <div className="mt-4 border border-zinc-700 rounded-lg overflow-hidden">
              <p className="bg-zinc-800 px-3 py-1 text-zinc-400 text-xs">Vista previa</p>
              <iframe src={iframe.url} width="100%" height="300" style={{ border: 'none' }} title={iframe.title} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
