"use client";

import type { ReactNode } from "react";
import Link from "next/link";

import { SignInButton, UserButton } from "@clerk/nextjs";

import { primaryNavigation } from "../config/navigation";
import { useAuthActor } from "../hooks/use-auth-actor";

export function AppShell({ children }: { children: ReactNode }) {
  const { isSignedIn } = useAuthActor();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="font-semibold text-slate-100 hover:text-white">
            StrikeEdge
          </Link>
          <input
            placeholder="Search symbol, screener, strategy"
            className="hidden w-80 rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm sm:block"
          />
          <div className="flex items-center gap-2">
            {isSignedIn ? (
              <UserButton afterSignOutUrl="/" />
            ) : (
              <SignInButton mode="modal">
                <button
                  type="button"
                  className="rounded border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700"
                >
                  Sign in
                </button>
              </SignInButton>
            )}
          </div>
        </div>
      </header>
      <div className="flex">
        <aside className="w-56 border-r border-slate-800 p-3">
          <nav className="space-y-1">
            {primaryNavigation.map((item) => (
              <Link key={item.href} href={item.href} className="block rounded px-2 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white">
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="flex-1 p-4">{children}</main>
      </div>
    </div>
  );
}
