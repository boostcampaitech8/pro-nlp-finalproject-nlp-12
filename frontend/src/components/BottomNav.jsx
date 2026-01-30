import { NavLink } from "react-router-dom";
import "../styles/BottomNav.css";

const tabs = [
  { to: "/recommend", label: "Recommend" },
  { to: "/search", label: "Search" },
  { to: "/timeline", label: "Timeline" },
  { to: "/mypage", label: "MyPage" },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav" role="navigation" aria-label="Bottom Navigation">
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? "is-active" : ""}`
          }
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}
