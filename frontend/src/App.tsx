import { Routes, Route } from "react-router-dom";
import { ChatPage } from "./features/chat/ChatPage";
import { TripListPage } from "./features/trips/TripListPage";
import { TripDetailPage } from "./features/trips/TripDetailPage";
import { MapView } from "./features/map/MapView";
import { LoginPage } from "./features/auth/LoginPage";
import { BottomNav } from "./components/BottomNav/BottomNav";
import { ToastContainer } from "./components/Toast/ToastContainer";

export default function App() {
  return (
    <ToastContainer>
      <div className="flex flex-col min-h-dvh w-full relative">
        {/* 主内容区 — 全屏无宽度限制 */}
        <main className="flex-1 overflow-hidden md:pb-0 pb-14">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/trips" element={<TripListPage />} />
            <Route path="/trips/:id" element={<TripDetailPage />} />
            <Route path="/trips/:id/map" element={<MapView />} />
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </main>

        {/* 底部导航 — 仅移动端显示 */}
        <div className="md:hidden">
          <BottomNav />
        </div>
      </div>
    </ToastContainer>
  );
}
