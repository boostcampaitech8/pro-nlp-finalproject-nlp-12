import "./globals.css";
import { Suspense } from "react";
import AuthGate from "../components/common/AuthGate";
import AppShell from "../components/layout/AppShell";
import AppHeader from "../components/layout/Header";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="text-black">
        <Suspense fallback={<div style={{ height: 72}} />}>
          <AppHeader />
        </Suspense>
        <AuthGate>
          <AppShell>{children}</AppShell>
        </AuthGate>
      </body>
    </html>
  );
}
