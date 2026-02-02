import "./globals.css";
import AuthGate from "../components/common/AuthGate";
import AppShell from "../components/layout/AppShell";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <AuthGate>
          <AppShell>{children}</AppShell>
        </AuthGate>
      </body>
    </html>
  );
}
