import type { ReactNode } from "react";
import { ClerkProvider } from "@clerk/nextjs";

import { AppShell } from "../layout/AppShell";
import "./globals.css";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ClerkProvider>
          <AppShell>{children}</AppShell>
        </ClerkProvider>
      </body>
    </html>
  );
}
