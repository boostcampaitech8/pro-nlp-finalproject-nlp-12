"use client";

import { usePathname } from "next/navigation";
import BottomNav from "./BottomNav";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideNav = pathname?.startsWith("/onboarding");

  return (
    <div
      style={{
        minHeight: "calc(100dvh - 56px)",
        display: "flex",
        flexDirection: "column",
        background:
          "radial-gradient(900px 520px at 90% 10%, rgba(79, 124, 255, 0.08), transparent 55%)",
      }}
    >
      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>{children}</main>
      {!hideNav && <BottomNav />}
    </div>
  );
}
