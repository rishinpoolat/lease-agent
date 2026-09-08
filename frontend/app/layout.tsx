import { faBuilding } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";
import "@/lib/fontawesome";

export const metadata = {
  title: "Lease Agent",
  description: "Lease extraction + property issue reporting, unified per unit.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans text-sm">
        <header className="border-b border-border bg-card">
          <div className="mx-auto flex max-w-4xl items-center px-5 py-3">
            <Link href="/" className="flex items-center gap-2 font-semibold text-foreground">
              <FontAwesomeIcon icon={faBuilding} className="h-4 w-4 text-primary" />
              Lease Agent
            </Link>
          </div>
        </header>
        <main className="mx-auto max-w-4xl px-5 py-6">{children}</main>
      </body>
    </html>
  );
}
