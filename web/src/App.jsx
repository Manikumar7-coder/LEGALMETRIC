import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

import LandingPage from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ScanPage from './pages/Scan';
import ResultPage from './pages/Result';
import HistoryPage from './pages/History';
import InspectionDetailsPage from './pages/InspectionDetails';
import ReportsPage from './pages/Reports';
import ProfilePage from './pages/Profile';
import UsersPage from './pages/Users';
import DesignSystemPage from './pages/DesignSystem';

// App Layout wrapper for protected routes
const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="app-container">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-content">
        <Header onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />
        <main className="page-body">
          <ProtectedRoute />
        </main>
      </div>
    </div>
  );
};

export const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* 1. Landing / Home (Public) */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/home" element={<LandingPage />} />

          {/* 2. Login (Public) */}
          <Route path="/login" element={<Login />} />

          {/* 3. Register (Public) */}
          <Route path="/register" element={<Register />} />

          {/* Protected Routes inside App Layout */}
          <Route element={<AppLayout />}>
            {/* 4. Dashboard */}
            <Route path="/dashboard" element={<Dashboard />} />

            {/* 5. New Inspection */}
            <Route path="/scan" element={<ScanPage />} />
            <Route path="/inspection/new" element={<ScanPage />} />
            <Route path="/new-inspection" element={<ScanPage />} />

            {/* 6. Inspection Result */}
            <Route path="/result/:id" element={<ResultPage />} />
            <Route path="/inspection/result/:id" element={<ResultPage />} />

            {/* 7. Inspection History */}
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/inspections" element={<HistoryPage />} />

            {/* 8. Inspection Details */}
            <Route path="/inspection/:id" element={<InspectionDetailsPage />} />
            <Route path="/history/:id" element={<InspectionDetailsPage />} />

            {/* 9. Reports */}
            <Route path="/reports" element={<ReportsPage />} />

            {/* 10. Settings / Profile */}
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<ProfilePage />} />

            {/* 11. User Management (Admin only) */}
            <Route path="/users" element={<UsersPage />} />

            {/* Design System UI Foundation Showcase */}
            <Route path="/design-system" element={<DesignSystemPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
