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
    <div className="flex flex-col min-h-dvh max-w-lg mx-auto relative">
      {/* 主内容区 */}
      <main className="flex-1 overflow-y-auto pb-14">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/trips" element={<TripListPage />} />
          <Route path="/trips/:id" element={<TripDetailPage />} />
          <Route path="/trips/:id/map" element={<MapView />} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </main>

      {/* 全局底部导航 */}
      <BottomNav />

      {/* 全局 Toast */}
      <ToastContainer />
    </div>
  );
}
