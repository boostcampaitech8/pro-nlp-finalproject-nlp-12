import "./globals.css";
import AuthGate from "../components/common/AuthGate";
import AppShell from "../components/layout/AppShell";
import AppHeader from "../components/layout/Header";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <AppHeader />
        <AuthGate>
          <AppShell>{children}</AppShell>
        </AuthGate>
      </body>
    </html>
  );
}
