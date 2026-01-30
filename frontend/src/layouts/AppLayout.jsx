import { Outlet } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import "./AppLayout.css";

export default function AppLayout() {
  return (
    <div className="app-layout">
      <main className="app-layout__main">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
