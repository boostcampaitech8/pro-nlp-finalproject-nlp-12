"use client";

import { usePathname } from "next/navigation";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideHeaderOffset = pathname?.startsWith("/onboarding");

  return (
    <div
      style={{
        minHeight: hideHeaderOffset ? "100dvh" : "calc(100dvh - 64px)",
        display: "flex",
        flexDirection: "column",
        background:
          "radial-gradient(900px 520px at 90% 10%, rgba(79, 124, 255, 0.08), transparent 55%)",
      }}
    >
      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>{children}</main>
    </div>
  );
}
