import { Routes, Route, Navigate } from "react-router-dom";

import RequireUser from "./routes/RequireUser";
import AppLayout from "./layouts/AppLayout";

import ShortsFeedPage from "./pages/ShortsFeedPage";
import OnboardingPage from "./pages/OnboardingPage";
import PaperDetailPage from "./pages/PaperDetailPage";
import LibraryPage from "./pages/LibraryPage";

// 새로 만들 페이지(아래에 코드도 줄게)
import SearchPage from "./pages/SearchPage";
import TimelinePage from "./pages/TimelinePage";

export default function App() {
  return (
    <Routes>
      {/* 기본 진입 */}
      <Route path="/" element={<Navigate to="/recommend" replace />} />

      {/* 설문 */}
      <Route path="/onboarding" element={<OnboardingPage />} />

      {/* userId 있어야 접근 가능한 영역 */}
      <Route element={<RequireUser />}>
        {/* 하단 네비가 깔리는 레이아웃 */}
        <Route element={<AppLayout />}>
          <Route path="/recommend" element={<ShortsFeedPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/mypage" element={<LibraryPage />} />

          {/* 상세 페이지는 네비가 있어도 되고, 빼고 싶으면 Layout 밖으로 빼도 됨 */}
          <Route path="/papers/:paperId" element={<PaperDetailPage />} />
        </Route>
      </Route>

      {/* 없는 경로 */}
      <Route path="*" element={<Navigate to="/recommend" replace />} />
    </Routes>
  );
}
