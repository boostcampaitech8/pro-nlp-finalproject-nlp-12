// src/routes/RequireUser.jsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getUserId } from "../utils/userId";

export default function RequireUser() {
  const loc = useLocation();
  const userId = getUserId();

  if (!userId) {
    return <Navigate to="/onboarding" replace state={{ from: loc.pathname }} />;
  }

  return <Outlet />;
}
