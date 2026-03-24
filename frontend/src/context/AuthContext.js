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
      // Admin data is stored locally after login
      const storedAdmin = localStorage.getItem('admin');
      if (storedAdmin) {
        setAdmin(JSON.parse(storedAdmin));
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
      
      // Update gym branding
      if (response.data.gym?.primary_color) {
        document.documentElement.style.setProperty('--gym-primary', response.data.gym.primary_color);
      }
    } catch (error) {
      console.error('Error fetching member data:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const loginAdmin = async (email, password) => {
    const response = await axios.post(`${API}/auth/admin/login`, { email, password });
    const { admin: adminData, token: newToken } = response.data;
    
    localStorage.setItem('token', newToken);
    localStorage.setItem('userType', 'admin');
    localStorage.setItem('admin', JSON.stringify(adminData));
    
    setToken(newToken);
    setUserType('admin');
    setAdmin(adminData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    
    return adminData;
  };

  const loginMember = async (code) => {
    const response = await axios.post(`${API}/auth/member/login?code=${code}`);
    const { member: memberData, gym: gymData, membership: membershipData, token: newToken } = response.data;
    
    localStorage.setItem('token', newToken);
    localStorage.setItem('userType', 'member');
    
    setToken(newToken);
    setUserType('member');
    setMember(memberData);
    setGym(gymData);
    setMembership(membershipData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    
    // Update gym branding
    if (gymData?.primary_color) {
      document.documentElement.style.setProperty('--gym-primary', gymData.primary_color);
    }
    
    return { member: memberData, gym: gymData };
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    localStorage.removeItem('admin');
    setToken(null);
    setUserType(null);
    setAdmin(null);
    setMember(null);
    setGym(null);
    setMembership(null);
    setPlan(null);
    delete axios.defaults.headers.common['Authorization'];
    
    // Reset gym branding
    document.documentElement.style.setProperty('--gym-primary', '#E1FF01');
  };

  const refreshMemberData = async () => {
    if (userType === 'member' && token) {
      await fetchMemberData();
    }
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
      isAuthenticated: !!token,
      isAdmin: userType === 'admin',
      isMember: userType === 'member',
      isSuperAdmin: admin?.role === 'super_admin'
    }}>
      {children}
    </AuthContext.Provider>
  );
};
