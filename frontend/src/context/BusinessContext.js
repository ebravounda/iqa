import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { getLabels } from '../lib/businessLabels';

const BusinessContext = createContext(null);

export const useBusiness = () => {
  const context = useContext(BusinessContext);
  if (!context) return { labels: getLabels('gym'), businessType: 'gym', gymData: null };
  return context;
};

export const BusinessProvider = ({ children }) => {
  const { admin } = useAuth();
  const [gymData, setGymData] = useState(null);
  const [businessType, setBusinessType] = useState('gym');

  useEffect(() => {
    if (admin?.gym_id) {
      const API = process.env.REACT_APP_BACKEND_URL + '/api';
      fetch(`${API}/gyms/${admin.gym_id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
        .then(r => r.json())
        .then(gym => {
          setGymData(gym);
          setBusinessType(gym?.business_type || 'gym');
        })
        .catch(() => {});
    } else {
      setBusinessType('gym');
      setGymData(null);
    }
  }, [admin?.gym_id]);

  const labels = getLabels(businessType);

  return (
    <BusinessContext.Provider value={{ labels, businessType, gymData, setBusinessType }}>
      {children}
    </BusinessContext.Provider>
  );
};
