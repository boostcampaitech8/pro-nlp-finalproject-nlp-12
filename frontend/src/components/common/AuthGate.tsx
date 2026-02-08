"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUserId } from "../../lib/user";

const PUBLIC_PATHS = ["/onboarding"]; // 여기만 예외

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const isPublic = PUBLIC_PATHS.some((p) => pathname?.startsWith(p));
    const uid = getUserId();

    if (!uid && !isPublic) {
      router.replace("/onboarding");
      return;
    }
    setReady(true);
  }, [pathname, router]);

  // redirect 깜빡임 방지
  if (!ready) return null;
  return <>{children}</>;
}
