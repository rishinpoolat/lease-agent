import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "Lease Agent",
  description: "Lease extraction + property issue reporting, unified per unit.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <Link href="/">Lease Agent</Link>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
