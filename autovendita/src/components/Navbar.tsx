"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Car, Menu, X } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const links = [
  { href: "/", label: "Home" },
  { href: "/annunci", label: "Annunci" },
  { href: "/vendi", label: "Vendi Auto" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mt-4 flex items-center justify-between rounded-2xl border border-white/10 bg-slate-900/80 px-5 py-3 backdrop-blur-xl shadow-lg shadow-black/20">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-lg shadow-sky-500/30 transition-transform group-hover:scale-105">
              <Car className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              Auto<span className="text-sky-400">Vendita</span>
            </span>
          </Link>

          <ul className="hidden items-center gap-1 md:flex">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className={`relative rounded-xl px-4 py-2 text-sm font-medium transition-colors ${
                      active
                        ? "text-white"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {active && (
                      <motion.span
                        layoutId="nav-pill"
                        className="absolute inset-0 rounded-xl bg-white/10"
                        transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                      />
                    )}
                    <span className="relative">{link.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>

          <Link
            href="/vendi"
            className="hidden rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:shadow-sky-500/40 hover:brightness-110 md:inline-flex"
          >
            Inserisci annuncio
          </Link>

          <button
            onClick={() => setOpen(!open)}
            className="rounded-xl p-2 text-slate-400 hover:bg-white/10 hover:text-white md:hidden"
            aria-label="Menu"
          >
            {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-2 rounded-2xl border border-white/10 bg-slate-900/95 p-4 backdrop-blur-xl md:hidden"
            >
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className={`block rounded-xl px-4 py-3 text-sm font-medium ${
                    pathname === link.href
                      ? "bg-white/10 text-white"
                      : "text-slate-400"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/vendi"
                onClick={() => setOpen(false)}
                className="mt-2 block rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-4 py-3 text-center text-sm font-semibold text-white"
              >
                Inserisci annuncio
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>
    </header>
  );
}
