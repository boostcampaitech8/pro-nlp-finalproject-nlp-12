"use client";

import Link from "next/link";

export default function AppHeader() {
  return (
    <header className="sticky top-0 z-50 w-full">
      <div className="h-12 px-4 flex items-center gap-3 bg-black/40 backdrop-blur border-b border-white/10">
        <Link href="/" className="font-semibold tracking-tight">
          10 seconds
        </Link>
      </div>
    </header>
  );
}
