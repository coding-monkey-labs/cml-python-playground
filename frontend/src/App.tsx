import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { Layout, AdminGuard } from "@/components/layout/Layout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import SearchPage from "@/pages/SearchPage";
import FeaturesPage from "@/pages/FeaturesPage";
import GraphPage from "@/pages/GraphPage";
import PRPage from "@/pages/PRPage";
import ForensicsPage from "@/pages/ForensicsPage";
import ProfilePage from "@/pages/ProfilePage";
import WorkflowsPage from "@/pages/admin/WorkflowsPage";
import SchedulesPage from "@/pages/admin/SchedulesPage";
import HealthPage from "@/pages/admin/HealthPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          {/* Authenticated layout */}
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="features" element={<FeaturesPage />} />
            <Route path="graph" element={<GraphPage />} />
            <Route path="pull-requests" element={<PRPage />} />
            <Route path="forensics" element={<ForensicsPage />} />
            <Route path="profile" element={<ProfilePage />} />

            {/* Admin routes */}
            <Route path="admin" element={<AdminGuard />}>
              <Route path="workflows" element={<WorkflowsPage />} />
              <Route path="schedules" element={<SchedulesPage />} />
              <Route path="health" element={<HealthPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
