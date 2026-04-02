import { useState, useEffect } from 'react';

const MAIN_DOMAINS = ['app.ingresoqr.com', 'localhost', '127.0.0.1', 'preview.emergentagent.com'];

export function useCustomDomain() {
  const [domainGym, setDomainGym] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isCustomDomain, setIsCustomDomain] = useState(false);

  useEffect(() => {
    const hostname = window.location.hostname;
    const isMain = MAIN_DOMAINS.some(d => hostname.includes(d));

    if (isMain) {
      setIsCustomDomain(false);
      setLoading(false);
      return;
    }

    setIsCustomDomain(true);
    const API = process.env.REACT_APP_BACKEND_URL + '/api';

    fetch(`${API}/gyms/resolve-domain/${hostname}`)
      .then(r => {
        if (!r.ok) throw new Error('Domain not found');
        return r.json();
      })
      .then(gym => {
        setDomainGym(gym);
        setLoading(false);
      })
      .catch(() => {
        setDomainGym(null);
        setLoading(false);
      });
  }, []);

  return { domainGym, isCustomDomain, loading };
}
