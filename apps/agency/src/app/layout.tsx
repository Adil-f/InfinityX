import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Infinity X AI Agency (local)",
  description: "Local Phase 2 agency console — no deploy, no outreach.",
};

const nav = [
  ["/", "Dashboard"],
  ["/leads", "Leads"],
  ["/research", "Research"],
  ["/builder", "Builder"],
  ["/drafts", "Drafts"],
  ["/approvals", "Approvals"],
  ["/jobs", "Jobs"],
  ["/audit", "Audit"],
  ["/exports", "Exports"],
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-black/10 bg-white">
            <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
              <strong className="mr-4">Infinity X Agency</strong>
              <nav className="flex flex-wrap gap-3 text-sm">
                {nav.map(([href, label]) => (
                  <Link key={href} href={href} className="text-ink no-underline hover:text-accent">
                    {label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
          <footer className="mx-auto max-w-6xl px-4 pb-8 text-xs text-black/50">
            Local Phase 2 · no paid APIs · no email send · no deploy · web zip.zip preserved
          </footer>
        </div>
      </body>
    </html>
  );
}
