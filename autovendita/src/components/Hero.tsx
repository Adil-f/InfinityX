"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Search, Shield, Zap } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { BRANDS } from "@/lib/data";

export default function Hero() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [brand, setBrand] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (search) params.set("q", search);
    if (brand && brand !== "Tutte") params.set("brand", brand);
    router.push(`/annunci?${params.toString()}`);
  };

  return (
    <section className="relative min-h-[90vh] overflow-hidden pt-28 pb-20">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-900/40 via-slate-950 to-slate-950" />
      <div className="absolute top-20 left-1/4 h-72 w-72 rounded-full bg-sky-500/10 blur-3xl" />
      <div className="absolute bottom-20 right-1/4 h-96 w-96 rounded-full bg-blue-600/10 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-4 py-1.5 text-sm font-medium text-sky-300">
              <Zap className="h-4 w-4" />
              Il marketplace auto #1 in Italia
            </span>

            <h1 className="mt-6 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
              Vendi e compra{" "}
              <span className="bg-gradient-to-r from-sky-400 to-blue-500 bg-clip-text text-transparent">
                la tua auto
              </span>{" "}
              in pochi click
            </h1>

            <p className="mt-6 max-w-lg text-lg text-slate-400">
              Pubblica il tuo annuncio gratis, raggiungi migliaia di acquirenti
              e trova l&apos;auto dei tuoi sogni con filtri intelligenti e
              contatto diretto.
            </p>

            <form
              onSubmit={handleSearch}
              className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-2 backdrop-blur-sm"
            >
              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                  <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Cerca marca, modello, città..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full rounded-xl bg-slate-900/60 py-3.5 pl-12 pr-4 text-white placeholder:text-slate-500 outline-none ring-sky-500/50 focus:ring-2"
                  />
                </div>
                <select
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  className="rounded-xl bg-slate-900/60 px-4 py-3.5 text-white outline-none ring-sky-500/50 focus:ring-2 sm:w-44"
                >
                  {BRANDS.map((b) => (
                    <option key={b} value={b === "Tutte" ? "" : b}>
                      {b}
                    </option>
                  ))}
                </select>
                <button
                  type="submit"
                  className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-6 py-3.5 font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:brightness-110"
                >
                  Cerca
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </form>

            <div className="mt-8 flex flex-wrap gap-6">
              {[
                { icon: Shield, text: "Annunci verificati" },
                { icon: Zap, text: "Pubblicazione gratuita" },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-2 text-sm text-slate-400">
                  <Icon className="h-4 w-4 text-sky-400" />
                  {text}
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="relative hidden lg:block"
          >
            <div className="relative aspect-[4/3] overflow-hidden rounded-3xl border border-white/10 shadow-2xl shadow-sky-500/10">
              <img
                src="https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=900&q=80"
                alt="Auto sportiva"
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 rounded-2xl border border-white/10 bg-slate-900/80 p-4 backdrop-blur-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">In evidenza oggi</p>
                    <p className="text-lg font-bold text-white">BMW Serie 3 320d</p>
                  </div>
                  <p className="text-xl font-bold text-sky-400">€ 32.900</p>
                </div>
              </div>
            </div>

            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
              className="absolute -top-4 -right-4 rounded-2xl border border-white/10 bg-slate-900/90 px-5 py-3 backdrop-blur-xl shadow-xl"
            >
              <p className="text-2xl font-bold text-white">2.500+</p>
              <p className="text-xs text-slate-400">Auto disponibili</p>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
