import { useEffect } from "react";
import "@fontsource/chivo/400.css";
import "@fontsource/chivo/700.css";
import "@fontsource/chivo/900.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@fontsource/manrope/700.css";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { BusinessProvider } from "./context/BusinessContext";

// Layouts
import { AdminLayout } from "./layouts/AdminLayout";
import { PWALayout } from "./layouts/PWALayout";
import { ErrorBoundary } from "./components/ErrorBoundary";

// Admin Pages
import AdminLogin from "./pages/admin/AdminLogin";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminMembers from "./pages/admin/AdminMembers";
import AdminPlans from "./pages/admin/AdminPlans";
import AdminAccess from "./pages/admin/AdminAccess";
import AdminDevices from "./pages/admin/AdminDevices";
import AdminSettings from "./pages/admin/AdminSettings";
import AdminTemplates from "./pages/admin/AdminTemplates";
import AdminGyms from "./pages/admin/AdminGyms";
import AdminClasses from "./pages/admin/AdminClasses";
import AdminAttendance from "./pages/admin/AdminAttendance";
import AdminAccounting from "./pages/admin/AdminAccounting";
import KioskPage from "./pages/pwa/KioskPage";
import AdminSchedules from "./pages/admin/AdminSchedules";
import AdminStaff from "./pages/admin/AdminStaff";
import AdminNotifications from "./pages/admin/AdminNotifications";
import AdminGuests from "./pages/admin/AdminGuests";
import AdminSaaSPlans from "./pages/admin/AdminSaaSPlans";
import AdminPOS from "./pages/admin/AdminPOS";
import AdminIframes from "./pages/admin/AdminIframes";
import AdminBroadcast from "./pages/admin/AdminBroadcast";
import AdminAnalytics from "./pages/admin/AdminAnalytics";
import AdminForms from "./pages/admin/AdminForms";
import AdminData from "./pages/admin/AdminData";
import AdminSecurity from "./pages/admin/AdminSecurity";
import AdminDeviceMonitor from "./pages/admin/AdminDeviceMonitor";
import AdminGamification from "./pages/admin/AdminGamification";
import AdminRoutines from "./pages/admin/AdminRoutines";
import TrainerDashboard from "./pages/admin/TrainerDashboard";

// PWA Pages
import MemberLogin from "./pages/pwa/MemberLogin";
import MemberHome from "./pages/pwa/MemberHome";
import MemberHistory from "./pages/pwa/MemberHistory";
import MemberStats from "./pages/pwa/MemberStats";
import MemberMembership from "./pages/pwa/MemberMembership";
import MemberProfile from "./pages/pwa/MemberProfile";
import MemberClasses from "./pages/pwa/MemberClasses";
import MemberNotifications from "./pages/pwa/MemberNotifications";
import MemberGuests from "./pages/pwa/MemberGuests";
import PaymentSuccess from "./pages/pwa/PaymentSuccess";
import PublicRegister from "./pages/pwa/PublicRegister";
import MemberGamification from "./pages/pwa/MemberGamification";
import MemberRoutines from "./pages/pwa/MemberRoutines";

// Smart Dashboard: shows TrainerDashboard for trainers, AdminDashboard for others
const SmartDashboard = () => {
  const { admin } = useAuth();
  if (admin?.role === 'trainer') return <TrainerDashboard />;
  return <AdminDashboard />;
};

// Protected Route Components
const AdminRoute = ({ children }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (!isAuthenticated || !isAdmin) {
    return <Navigate to="/admin/login" replace />;
  }
  
  return <AdminLayout><ErrorBoundary>{children}</ErrorBoundary></AdminLayout>;
};

const MemberRoute = ({ children }) => {
  const { isAuthenticated, isMember, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--gym-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (!isAuthenticated || !isMember) {
    return <Navigate to="/app/login" replace />;
  }
  
  return <PWALayout><ErrorBoundary>{children}</ErrorBoundary></PWALayout>;
};

// Landing Page
const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#09090B] flex flex-col items-center justify-center p-8 noise-overlay">
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-5"
        style={{ backgroundImage: 'url(https://images.pexels.com/photos/6388373/pexels-photo-6388373.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
      />
      
      <div className="relative z-10 text-center max-w-xl">
        <h1 className="text-5xl sm:text-6xl font-black tracking-tight mb-4">
          <span style={{ color: 'var(--gym-primary)' }}>Ingreso</span>QR
        </h1>
        <p className="text-zinc-400 text-lg mb-12">
          Sistema de control de acceso inteligente para gimnasios
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a 
            href="/admin/login"
            className="btn-gym-primary text-center"
            data-testid="admin-access-btn"
          >
            Panel de Administración
          </a>
          <a 
            href="/app/login"
            className="px-6 py-3 rounded-full border border-zinc-700 hover:border-zinc-500 text-white font-semibold transition-colors text-center"
            data-testid="member-access-btn"
          >
            Acceso Socios
          </a>
        </div>
        
        <div className="mt-16 grid grid-cols-3 gap-8 text-center">
          <div>
            <p className="text-3xl font-black" style={{ color: 'var(--gym-primary)' }}>QR</p>
            <p className="text-zinc-500 text-sm">Dinámico</p>
          </div>
          <div>
            <p className="text-3xl font-black" style={{ color: 'var(--gym-primary)' }}>24/7</p>
            <p className="text-zinc-500 text-sm">Acceso</p>
          </div>
          <div>
            <p className="text-3xl font-black" style={{ color: 'var(--gym-primary)' }}>100%</p>
            <p className="text-zinc-500 text-sm">Seguro</p>
          </div>
        </div>
      </div>
    </div>
  );
};

function AppRoutes() {
  return (
    <Routes>
      {/* Landing */}
      <Route path="/" element={<LandingPage />} />
      
      {/* Admin Routes */}
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin" element={<AdminRoute><SmartDashboard /></AdminRoute>} />
      <Route path="/admin/gyms" element={<AdminRoute><AdminGyms /></AdminRoute>} />
      <Route path="/admin/members" element={<AdminRoute><AdminMembers /></AdminRoute>} />
      <Route path="/admin/plans" element={<AdminRoute><AdminPlans /></AdminRoute>} />
      <Route path="/admin/classes" element={<AdminRoute><AdminClasses /></AdminRoute>} />
      <Route path="/admin/attendance" element={<AdminRoute><AdminAttendance /></AdminRoute>} />
      <Route path="/admin/accounting" element={<AdminRoute><AdminAccounting /></AdminRoute>} />
      <Route path="/admin/schedules" element={<AdminRoute><AdminSchedules /></AdminRoute>} />
      <Route path="/admin/staff" element={<AdminRoute><AdminStaff /></AdminRoute>} />
      <Route path="/admin/notifications" element={<AdminRoute><AdminNotifications /></AdminRoute>} />
      <Route path="/admin/guests" element={<AdminRoute><AdminGuests /></AdminRoute>} />
      <Route path="/admin/access" element={<AdminRoute><AdminAccess /></AdminRoute>} />
      <Route path="/admin/devices" element={<AdminRoute><AdminDevices /></AdminRoute>} />
      <Route path="/admin/templates" element={<AdminRoute><AdminTemplates /></AdminRoute>} />
      <Route path="/admin/settings" element={<AdminRoute><AdminSettings /></AdminRoute>} />
      <Route path="/admin/saas-plans" element={<AdminRoute><AdminSaaSPlans /></AdminRoute>} />
      <Route path="/admin/pos" element={<AdminRoute><AdminPOS /></AdminRoute>} />
      <Route path="/admin/iframes" element={<AdminRoute><AdminIframes /></AdminRoute>} />
      <Route path="/admin/broadcast" element={<AdminRoute><AdminBroadcast /></AdminRoute>} />
      <Route path="/admin/analytics" element={<AdminRoute><AdminAnalytics /></AdminRoute>} />
      <Route path="/admin/forms" element={<AdminRoute><AdminForms /></AdminRoute>} />
      <Route path="/admin/data" element={<AdminRoute><AdminData /></AdminRoute>} />
      <Route path="/admin/security" element={<AdminRoute><AdminSecurity /></AdminRoute>} />
      <Route path="/admin/device-monitor" element={<AdminRoute><AdminDeviceMonitor /></AdminRoute>} />
      <Route path="/admin/gamification" element={<AdminRoute><AdminGamification /></AdminRoute>} />
      <Route path="/admin/routines" element={<AdminRoute><AdminRoutines /></AdminRoute>} />
      
      {/* PWA/Member Routes */}
      <Route path="/app/login" element={<MemberLogin />} />
      <Route path="/app" element={<MemberRoute><MemberHome /></MemberRoute>} />
      <Route path="/app/classes" element={<MemberRoute><MemberClasses /></MemberRoute>} />
      <Route path="/app/notifications" element={<MemberRoute><MemberNotifications /></MemberRoute>} />
      <Route path="/app/guests" element={<MemberRoute><MemberGuests /></MemberRoute>} />
      <Route path="/app/history" element={<MemberRoute><MemberHistory /></MemberRoute>} />
      <Route path="/app/stats" element={<MemberRoute><MemberStats /></MemberRoute>} />
      <Route path="/app/achievements" element={<MemberRoute><MemberGamification /></MemberRoute>} />
      <Route path="/app/routines" element={<MemberRoute><MemberRoutines /></MemberRoute>} />
      <Route path="/app/membership" element={<MemberRoute><MemberMembership /></MemberRoute>} />
      <Route path="/app/profile" element={<MemberRoute><MemberProfile /></MemberRoute>} />
      <Route path="/app/payment-success" element={<MemberRoute><PaymentSuccess /></MemberRoute>} />
      
      {/* Public Registration */}
      <Route path="/register/:gymId" element={<PublicRegister />} />
      
      {/* Kiosk Mode */}
      <Route path="/kiosk/:gymId" element={<KioskPage />} />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <BusinessProvider>
        <AppRoutes />
        <Toaster 
          position="top-center" 
          toastOptions={{
            style: {
              background: '#18181B',
              border: '1px solid #27272A',
              color: '#FAFAFA',
            },
          }}
        />
      </BusinessProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
