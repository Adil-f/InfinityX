import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Infinity X Global OSINT",
  description: "Authorized public-source intelligence for security teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <body className={inter.className}>
        <script
          dangerouslySetInnerHTML={{
            __html: "try{document.documentElement.dataset.theme=localStorage.getItem('ix-theme')||'dark'}catch(e){}",
          }}
        />
        {children}
      </body>
    </html>
  );
}
