import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Force logout on 403 (suspended/blocked member)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 403 && error.response?.data?.detail) {
      const detail = error.response.data.detail;
      const isMember = localStorage.getItem('userType') === 'member';
      if (isMember && (detail.includes('suspendida') || detail.includes('bloqueada'))) {
        localStorage.removeItem('token');
        localStorage.removeItem('userType');
        delete axios.defaults.headers.common['Authorization'];
        alert(detail);
        window.location.href = '/app/login';
        return new Promise(() => {});
      }
    }
    return Promise.reject(error);
  }
);

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
export const suspendMember = (id, reason) => axios.post(`${API}/members/${id}/suspend`, { reason });
export const deleteMember = (id) => axios.delete(`${API}/members/${id}`);
export const checkExpiredMemberships = () => axios.post(`${API}/members/check-expired-memberships`);
export const registerMember = (data) => axios.post(`${API}/members/register`, data);
export const importMembers = (formData) => axios.post(`${API}/members/import`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const assignMembershipsBulk = (data) => axios.post(`${API}/members/assign-memberships-bulk`, data);
export const updateMemberMembership = (memberId, data) => axios.put(`${API}/members/${memberId}/membership`, data);
export const getMembershipLogs = (memberId) => axios.get(`${API}/members/${memberId}/membership-logs`);
export const getRedsysConfig = (gymId) => axios.get(`${API}/gyms/${gymId}/redsys-config`);
export const updateRedsysConfig = (gymId, data) => axios.put(`${API}/gyms/${gymId}/redsys-config`, data);
export const initiateRedsysPayment = (data) => axios.post(`${API}/redsys/initiate`, data);
export const getRedsysPaymentStatus = (orderNumber) => axios.get(`${API}/redsys/status/${orderNumber}`);
export const getPaymentGateway = (gymId) => axios.get(`${API}/gyms/${gymId}/payment-gateway`);
export const setPaymentGateway = (gymId, gateway) => axios.put(`${API}/gyms/${gymId}/payment-gateway`, { gateway });

// Plans
export const getPlans = (gymId) => {
  let url = `${API}/plans`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getPlansPublic = (gymId) => axios.get(`${API}/plans/public/${gymId}`);
export const createPlan = (data) => axios.post(`${API}/plans`, data);
export const deletePlan = (id) => axios.delete(`${API}/plans/${id}`);
export const importPlans = (data) => axios.post(`${API}/plans/import`, data);

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
export const getDailyAccessStats = (gymId, days = 7) => {
  let url = `${API}/access/stats/daily?days=${days}`;
  if (gymId) url += `&gym_id=${gymId}`;
  return axios.get(url);
};
export const getHourlyAccessStats = (gymId) => {
  let url = `${API}/access/stats/hourly`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getMemberAccessStats = (memberId, days = 30) =>
  axios.get(`${API}/access/stats/member/${memberId}?days=${days}`);

// QR
export const generateQR = () => axios.get(`${API}/qr/generate`);

// Devices
export const getDevices = (gymId) => {
  let url = `${API}/devices`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createDevice = (data) => axios.post(`${API}/devices`, data);
export const deleteDevice = (id) => axios.delete(`${API}/devices/${id}`);

// Dashboard
export const getDashboardStats = () => axios.get(`${API}/dashboard/stats`);

// Payments
export const createCheckout = (planId) => axios.post(`${API}/payments/checkout?plan_id=${planId}`);
export const getPaymentStatus = (sessionId) => axios.get(`${API}/payments/status/${sessionId}`);
export const getPaymentHistory = (gymId) => {
  let url = `${API}/payments/history`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};

// Stripe Config
export const getStripeConfig = (gymId) => axios.get(`${API}/gyms/${gymId}/stripe-config`);
export const updateStripeConfig = (gymId, data) => axios.put(`${API}/gyms/${gymId}/stripe-config`, data);
export const gymHasPayments = (gymId) => axios.get(`${API}/gyms/${gymId}/has-payments`);

// Validation (for Raspberry Pi - no auth needed)
export const validateAccess = (data) => axios.post(`${API}/access/validate`, data);

// Manual Payments
export const createManualPayment = (data) => axios.post(`${API}/payments/manual`, data);

// Classes
export const getClasses = (gymId) => {
  let url = `${API}/classes`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createClass = (data) => axios.post(`${API}/classes`, data);
export const deleteClass = (id) => axios.delete(`${API}/classes/${id}`);

// Schedules
export const getSchedules = (gymId, dateFrom, dateTo) => {
  let url = `${API}/schedules`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  if (params.toString()) url += `?${params.toString()}`;
  return axios.get(url);
};
export const createSchedule = (data) => axios.post(`${API}/schedules`, data);
export const cancelSchedule = (id) => axios.put(`${API}/schedules/${id}/cancel`);

// Bookings
export const getBookings = (gymId, scheduleId) => {
  let url = `${API}/bookings`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (scheduleId) params.append('schedule_id', scheduleId);
  if (params.toString()) url += `?${params.toString()}`;
  return axios.get(url);
};

// Trainers
export const getTrainers = (gymId) => {
  let url = `${API}/trainers`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createTrainer = (data) => axios.post(`${API}/trainers`, data);

// Staff
export const getStaff = (gymId) => {
  let url = `${API}/staff`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createStaff = (data) => axios.post(`${API}/staff`, data);

// Notifications
export const getNotifications = (gymId) => {
  let url = `${API}/notifications`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createNotification = (data) => axios.post(`${API}/notifications`, data);
export const deleteNotification = (id) => axios.delete(`${API}/notifications/${id}`);

// Guests  
export const getAllGuests = (gymId) => {
  let url = `${API}/guests`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};

// Accounting
export const getAccountingReport = (gymId, dateFrom, dateTo) => {
  let url = `${API}/accounting/report`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  if (params.toString()) url += `?${params.toString()}`;
  return axios.get(url);
};
export const createCashWithdrawal = (data) => axios.post(`${API}/accounting/withdrawal`, data);
export const getCashWithdrawals = (gymId) => {
  let url = `${API}/accounting/withdrawals`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const pruneOldRecords = (months = 6) => axios.delete(`${API}/accounting/prune?months=${months}`);

// SaaS Plans
export const getSaaSPlans = () => axios.get(`${API}/saas/plans`);
export const createSaaSPlan = (data) => axios.post(`${API}/saas/plans`, data);
export const updateSaaSPlan = (id, data) => axios.put(`${API}/saas/plans/${id}`, data);
export const deleteSaaSPlan = (id) => axios.delete(`${API}/saas/plans/${id}`);
export const assignSaaSPlan = (gymId, planId) => axios.put(`${API}/gyms/${gymId}/saas-plan`, { saas_plan_id: planId });
export const getGymSaaSFeatures = (gymId) => axios.get(`${API}/gyms/${gymId}/saas-features`);
export const getMySubscription = () => axios.get(`${API}/saas/my-subscription`);
export const getAvailableSaaSPlans = () => axios.get(`${API}/saas/available-plans`);
export const subscribeSaaSPlan = (planId) => axios.post(`${API}/saas/subscribe`, { plan_id: planId });

// Email system
export const getMemberEmails = (memberId) => axios.get(`${API}/emails/member/${memberId}`);
export const resendEmail = (emailId) => axios.post(`${API}/emails/resend/${emailId}`);
export const updatePlan = (id, data) => axios.put(`${API}/plans/${id}`, data);
export const updateClass = (id, data) => axios.put(`${API}/classes/${id}`, data);
export const cleanupInactiveMembers = (days = 60) => axios.post(`${API}/members/cleanup-inactive`, { days });
export const assignRFID = (memberId, rfidUid) => axios.put(`${API}/members/${memberId}/rfid`, { rfid_uid: rfidUid });

// All Transactions (paid + pending)
export const getAllTransactions = (params = {}) => {
  const searchParams = new URLSearchParams();
  if (params.gym_id) searchParams.append('gym_id', params.gym_id);
  if (params.status) searchParams.append('status', params.status);
  if (params.date_from) searchParams.append('date_from', params.date_from);
  if (params.date_to) searchParams.append('date_to', params.date_to);
  return axios.get(`${API}/accounting/transactions?${searchParams.toString()}`);
};

// Broadcasts
export const createBroadcast = (data) => axios.post(`${API}/broadcast`, data);
export const getActiveBroadcasts = () => axios.get(`${API}/broadcast/active`);
export const dismissBroadcast = (id) => axios.post(`${API}/broadcast/${id}/dismiss`);

// POS
export const getPOSProducts = (gymId) => {
  let url = `${API}/pos/products`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createPOSProduct = (data) => axios.post(`${API}/pos/products`, data);
export const updatePOSProduct = (id, data) => axios.put(`${API}/pos/products/${id}`, data);
export const deletePOSProduct = (id) => axios.delete(`${API}/pos/products/${id}`);
export const createPOSSale = (data) => axios.post(`${API}/pos/sales`, data);
export const getPOSSales = (gymId, dateFrom, dateTo) => {
  let url = `${API}/pos/sales`;
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  if (params.toString()) url += `?${params.toString()}`;
  return axios.get(url);
};
export const getPOSStats = (gymId) => {
  let url = `${API}/pos/stats`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};

// MercadoPago
export const getMercadoPagoConfig = (gymId) => axios.get(`${API}/gyms/${gymId}/mercadopago-config`);
export const updateMercadoPagoConfig = (gymId, data) => axios.put(`${API}/gyms/${gymId}/mercadopago-config`, data);
export const createMPPreference = (planId) => axios.post(`${API}/mercadopago/create-preference?plan_id=${planId}`);

// Gym Public Info
export const getGymPublicInfo = (gymId) => axios.get(`${API}/gyms/${gymId}/public-info`);

// Analytics
export const getAnalyticsOverview = (gymId) => {
  let url = `${API}/analytics/overview`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getHourlyHeatmap = (gymId) => {
  let url = `${API}/analytics/hourly-heatmap`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getRevenueComparison = (gymId) => {
  let url = `${API}/analytics/revenue-comparison`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getMemberRetention = (gymId) => {
  let url = `${API}/analytics/member-retention`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const getPeakHours = (gymId) => {
  let url = `${API}/analytics/peak-hours`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};

// Custom Forms
export const getCustomForms = (gymId) => {
  let url = `${API}/forms`;
  if (gymId) url += `?gym_id=${gymId}`;
  return axios.get(url);
};
export const createCustomForm = (data) => axios.post(`${API}/forms`, data);
export const updateCustomForm = (id, data) => axios.put(`${API}/forms/${id}`, data);
export const deleteCustomForm = (id) => axios.delete(`${API}/forms/${id}`);
export const getPublicForms = (gymId) => axios.get(`${API}/forms/public/${gymId}`);
export const submitFormResponse = (formId, data) => axios.post(`${API}/forms/${formId}/responses`, data);
export const getFormResponses = (formId) => axios.get(`${API}/forms/${formId}/responses`);

// Upload
export const uploadAvatar = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return axios.post(`${API}/upload/avatar`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};
export const uploadAvatarAdmin = (memberId, file) => {
  const fd = new FormData();
  fd.append('file', file);
  return axios.post(`${API}/upload/avatar/admin/${memberId}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};

// QR Mode
export const setMemberQRMode = (memberId, mode) => axios.put(`${API}/members/${memberId}/qr-mode`, { qr_mode: mode });

// Sales Report PDF
export const downloadSalesReportPDF = (gymId, period, dateFrom, dateTo) => {
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (period) params.append('period', period);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  return axios.get(`${API}/accounting/sales-report-pdf?${params.toString()}`, { responseType: 'blob' });
};

// Members Export Excel
export const exportMembersExcel = (gymId, status, dateFrom, dateTo, includeMemberships) => {
  const params = new URLSearchParams();
  if (gymId) params.append('gym_id', gymId);
  if (status && status !== 'all') params.append('status', status);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  if (includeMemberships) params.append('include_memberships', 'true');
  return axios.get(`${API}/members/export/excel?${params.toString()}`, { responseType: 'blob' });
};

// Member Devices (Admin)
export const getMemberDevices = (memberId) => axios.get(`${API}/member-devices/${memberId}`);
export const deactivateDevice = (deviceId) => axios.put(`${API}/member-devices/${deviceId}/deactivate`);
export const deactivateAllDevices = (memberId) => axios.put(`${API}/member-devices/member/${memberId}/deactivate-all`);
export const updateMaxDevices = (gymId, maxDevices) => axios.put(`${API}/gyms/${gymId}/max-devices`, { max_devices_per_member: maxDevices });
export const getMemberVisitStats = (memberId) => axios.get(`${API}/access/stats/member`);
export const getMemberVisitStatsAdmin = (memberId) => axios.get(`${API}/stats/member-visits/${memberId}`);

// Product Image Upload
export const uploadProductImage = (productId, file) => {
  const fd = new FormData();
  fd.append('file', file);
  return axios.post(`${API}/upload/product-image/${productId}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};
