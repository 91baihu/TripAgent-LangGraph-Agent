import { Routes, Route } from "react-router-dom";
import { ChatPage } from "./features/chat/ChatPage";
import { TripListPage } from "./features/trips/TripListPage";
import { TripDetailPage } from "./features/trips/TripDetailPage";
import { MapView } from "./features/map/MapView";
import { LoginPage } from "./features/auth/LoginPage";
import { MePage } from "./features/auth/MePage";
import { PricingPage } from "./features/billing/PricingPage";
import { AdminPage } from "./features/admin/AdminPage";
import { SessionListPage } from "./features/sessions/SessionListPage";
import { BottomNav } from "./components/BottomNav/BottomNav";
import { ToastContainer } from "./components/Toast/ToastContainer";
import { ErrorBoundary } from "./components/ErrorBoundary/ErrorBoundary";
import { ProtectedRoute } from "./components/ProtectedRoute/ProtectedRoute";

export default function App() {
  return (
    <ErrorBoundary>
      <ToastContainer>
        <div className="flex flex-col min-h-dvh w-full relative">
          {/* 主内容区 — 全屏无宽度限制 */}
          <main className="flex-1 overflow-hidden md:pb-0 pb-14">
            <Routes>
              <Route path="/" element={<ChatPage />} />
              <Route
                path="/trips"
                element={
                  <ProtectedRoute>
                    <TripListPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/trips/:id"
                element={
                  <ProtectedRoute>
                    <TripDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/trips/:id/map"
                element={
                  <ProtectedRoute>
                    <MapView />
                  </ProtectedRoute>
                }
              />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route
                path="/sessions"
                element={
                  <ProtectedRoute>
                    <SessionListPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/me"
                element={
                  <ProtectedRoute>
                    <MePage />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>

          {/* 底部导航 — 仅移动端显示 */}
          <div className="md:hidden">
            <BottomNav />
          </div>
        </div>
      </ToastContainer>
    </ErrorBoundary>
  );
}
