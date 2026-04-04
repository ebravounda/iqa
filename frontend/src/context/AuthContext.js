import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [admin, setAdmin] = useState(null);
  const [member, setMember] = useState(null);
  const [gym, setGym] = useState(null);
  const [membership, setMembership] = useState(null);
  const [plan, setPlan] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [userType, setUserType] = useState(localStorage.getItem('userType'));
  const [loading, setLoading] = useState(true);
  const [isImpersonating, setIsImpersonating] = useState(false);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      if (userType === 'admin') {
        fetchAdminData();
      } else if (userType === 'member') {
        fetchMemberData();
      } else {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [token, userType]);

  const fetchAdminData = async () => {
    try {
      const storedAdmin = localStorage.getItem('admin');
      if (storedAdmin) {
        const parsed = JSON.parse(storedAdmin);
        setAdmin(parsed);
        setIsImpersonating(!!parsed.impersonating);
      }
    } catch (error) {
      console.error('Error fetching admin data:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const fetchMemberData = async () => {
    try {
      const response = await axios.get(`${API}/auth/member/me`);
      setMember(response.data.member);
      setGym(response.data.gym);
      setMembership(response.data.membership);
      setPlan(response.data.plan);
      
      if (response.data.gym?.primary_color) {
        document.documentElement.style.setProperty('--gym-primary', response.data.gym.primary_color);
      }
      if (response.data.gym?.bg_color) {
        document.documentElement.style.setProperty('--admin-bg', response.data.gym.bg_color);
      }
      if (response.data.gym?.menu_color) {
        document.documentElement.style.setProperty('--admin-menu', response.data.gym.menu_color);
      }
      if (response.data.gym?.text_color) {
        document.documentElement.style.setProperty('--admin-text', response.data.gym.text_color);
      }
      if (response.data.gym?.secondary_color) {
        document.documentElement.style.setProperty('--gym-secondary', response.data.gym.secondary_color);
      }
    } catch (error) {
      console.error('Error fetching member data:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  // Periodic status check for members - detects suspension in real-time
  useEffect(() => {
    if (!token || userType !== 'member') return;
    const interval = setInterval(async () => {
      try {
        await axios.get(`${API}/auth/member/me`);
      } catch (err) {
        // 403 will be caught by the Axios interceptor and force logout
      }
    }, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [token, userType]);

  const loginAdmin = async (email, password) => {
    const response = await axios.post(`${API}/auth/admin/login`, { email, password });
    const { admin: adminData, token: newToken } = response.data;
    
    localStorage.setItem('token', newToken);
    localStorage.setItem('userType', 'admin');
    localStorage.setItem('admin', JSON.stringify(adminData));
    
    setToken(newToken);
    setUserType('admin');
    setAdmin(adminData);
    setIsImpersonating(false);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    
    return adminData;
  };

  const impersonateGym = async (gymId) => {
    // Save current super admin state before impersonating
    const currentAdmin = localStorage.getItem('admin');
    const currentToken = localStorage.getItem('token');
    localStorage.setItem('original_admin', currentAdmin);
    localStorage.setItem('original_token', currentToken);
    
    const response = await axios.post(`${API}/auth/admin/impersonate/${gymId}`);
    const { admin: adminData, token: newToken } = response.data;
    
    localStorage.setItem('token', newToken);
    localStorage.setItem('admin', JSON.stringify(adminData));
    
    setToken(newToken);
    setAdmin(adminData);
    setIsImpersonating(true);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    
    return adminData;
  };

  const exitImpersonation = () => {
    const originalAdmin = localStorage.getItem('original_admin');
    const originalToken = localStorage.getItem('original_token');
    
    if (originalAdmin && originalToken) {
      localStorage.setItem('token', originalToken);
      localStorage.setItem('admin', originalAdmin);
      localStorage.removeItem('original_admin');
      localStorage.removeItem('original_token');
      
      const parsed = JSON.parse(originalAdmin);
      setToken(originalToken);
      setAdmin(parsed);
      setIsImpersonating(false);
      axios.defaults.headers.common['Authorization'] = `Bearer ${originalToken}`;
    }
  };

  const getDeviceFingerprint = () => {
    let fp = localStorage.getItem('device_fingerprint');
    if (!fp) {
      fp = 'dev_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
      localStorage.setItem('device_fingerprint', fp);
    }
    return fp;
  };

  const loginMember = async (code) => {
    const fp = getDeviceFingerprint();
    const response = await axios.post(`${API}/auth/member/login?code=${code}&device_fingerprint=${fp}`);
    const { member: memberData, gym: gymData, membership: membershipData, token: newToken } = response.data;
    
    localStorage.setItem('token', newToken);
    localStorage.setItem('userType', 'member');
    
    setToken(newToken);
    setUserType('member');
    setMember(memberData);
    setGym(gymData);
    setMembership(membershipData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    
    if (gymData?.primary_color) {
      document.documentElement.style.setProperty('--gym-primary', gymData.primary_color);
    }
    
    return { member: memberData, gym: gymData };
  };

  const logout = async () => {
    const isDemo = localStorage.getItem('is_demo') === 'true';
    if (isDemo) {
      try { await axios.post(`${API}/demo/cleanup`); } catch {}
    }
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    localStorage.removeItem('admin');
    localStorage.removeItem('original_admin');
    localStorage.removeItem('original_token');
    localStorage.removeItem('is_demo');
    setToken(null);
    setUserType(null);
    setAdmin(null);
    setMember(null);
    setGym(null);
    setMembership(null);
    setPlan(null);
    setIsImpersonating(false);
    delete axios.defaults.headers.common['Authorization'];
    
    document.documentElement.style.setProperty('--gym-primary', '#E1FF01');
  };

  const refreshMemberData = async () => {
    if (userType === 'member' && token) {
      await fetchMemberData();
    }
  };

  const DEFAULT_MANAGER_PERMISSIONS = [
    "members_view", "members_create", "members_edit",
    "payments_register", "pos_sell", "access_view", "classes_manage"
  ];

  const hasPermission = (permission) => {
    if (!admin) return false;
    if (admin.role === 'super_admin' || admin.role === 'gym_admin') return true;
    const perms = admin.permissions || DEFAULT_MANAGER_PERMISSIONS;
    return perms.includes(permission);
  };

  return (
    <AuthContext.Provider value={{
      admin,
      member,
      gym,
      membership,
      plan,
      token,
      userType,
      loading,
      loginAdmin,
      loginMember,
      logout,
      refreshMemberData,
      impersonateGym,
      exitImpersonation,
      isImpersonating,
      hasPermission,
      isAuthenticated: !!token,
      isAdmin: userType === 'admin',
      isMember: userType === 'member',
      isSuperAdmin: admin?.role === 'super_admin' && !admin?.impersonating
    }}>
      {children}
    </AuthContext.Provider>
  );
};
