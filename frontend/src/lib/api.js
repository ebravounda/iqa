import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Gyms
export const getGyms = () => axios.get(`${API}/gyms`);
export const getGym = (id) => axios.get(`${API}/gyms/${id}`);
export const createGym = (data) => axios.post(`${API}/gyms`, data);
export const updateGym = (id, data) => axios.put(`${API}/gyms/${id}`, data);
export const suspendGym = (id) => axios.put(`${API}/gyms/${id}/suspend`);
export const deleteGym = (id) => axios.delete(`${API}/gyms/${id}`);
export const updateEmailTemplate = (gymId, type, data) => axios.put(`${API}/gyms/${gymId}/templates/${type}`, data);
export const regenerateGymToken = (id) => axios.post(`${API}/gyms/${id}/regenerate-token`);

// Members
export const getMembers = (gymId, status) => {
  let url = `${API}/members`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (status) params.append('status', status);
  if (params.toString()) url += `?${params.toString()}`;
  return axios.get(url);
};
export const getMember = (id) => axios.get(`${API}/members/${id}`);
export const createMember = (data) => axios.post(`${API}/members`, data);
export const updateMember = (id, data) => axios.put(`${API}/members/${id}`, data);
export const approveMember = (id) => axios.post(`${API}/members/${id}/approve`);
export const blockMember = (id) => axios.post(`${API}/members/${id}/block`);
export const registerMember = (data) => axios.post(`${API}/members/register`, data);

// Plans
export const getPlans = (gymId) => {
  let url = `${API}/plans`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getPlansPublic = (gymId) => axios.get(`${API}/plans/public/${gymId}`);
export const createPlan = (data) => axios.post(`${API}/plans`, data);
export const deletePlan = (id) => axios.delete(`${API}/plans/${id}`);

// Memberships
export const getMemberships = (gymId, memberId) => {
  let url = `${API}/memberships`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (memberId) params.append('member_id', memberId);
  if (params.toString()) url += `?${params.toString()}`;
  return axios.get(url);
};
export const createMembership = (data) => axios.post(`${API}/memberships`, data);
export const getExpiringMemberships = (days = 10) => axios.get(`${API}/memberships/expiring?days=${days}`);

// Access
export const getAccessLogs = (gymId, memberId, dateFrom, dateTo, limit = 100) => {
  let url = `${API}/access/logs`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (memberId) params.append('member_id', memberId);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  params.append('limit', limit);
  url += `?${params.toString()}`;
  return axios.get(url);
};
export const getMemberAccessLogs = () => axios.get(`${API}/access/logs/member`);
export const getAccessStats = (gymId) => {
  let url = `${API}/access/stats`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};

// QR
export const generateQR = () => axios.get(`${API}/qr/generate`);

// Devices
export const getDevices = (gymId) => {
  let url = `${API}/devices`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createDevice = (data) => axios.post(`${API}/devices`, data);

// Dashboard
export const getDashboardStats = () => axios.get(`${API}/dashboard/stats`);

// Payments
export const createCheckout = (planId) => axios.post(`${API}/payments/checkout?plan_id=${planId}`);
export const getPaymentStatus = (sessionId) => axios.get(`${API}/payments/status/${sessionId}`);

// Validation (for Raspberry Pi - no auth needed)
export const validateAccess = (data) => axios.post(`${API}/access/validate`, data);
