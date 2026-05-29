"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle, Upload } from "lucide-react";
import { useCars } from "@/context/CarsContext";
import { BRANDS } from "@/lib/data";
import { FuelType, Transmission } from "@/lib/types";

const defaultImage =
  "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800&q=80";

export default function SellCarForm() {
  const router = useRouter();
  const { addCar } = useCars();
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    brand: "",
    model: "",
    year: new Date().getFullYear(),
    price: 15000,
    mileage: 50000,
    fuel: "Benzina" as FuelType,
    transmission: "Manuale" as Transmission,
    power: 100,
    color: "",
    location: "",
    description: "",
    seller: "",
    phone: "",
    image: "",
  });

  const update = (field: string, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addCar({
      ...form,
      image: form.image || defaultImage,
      images: [form.image || defaultImage],
      featured: false,
    });
    setSubmitted(true);
    setTimeout(() => router.push("/annunci"), 2000);
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center rounded-2xl border border-emerald-500/20 bg-emerald-500/5 py-20 text-center"
      >
        <CheckCircle className="h-16 w-16 text-emerald-400" />
        <h2 className="mt-4 text-2xl font-bold text-white">
          Annuncio pubblicato!
        </h2>
        <p className="mt-2 text-slate-400">
          Il tuo annuncio è online. Reindirizzamento in corso...
        </p>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div className="rounded-2xl border border-white/5 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-white">Informazioni veicolo</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm text-slate-400">Marca *</label>
            <select
              required
              value={form.brand}
              onChange={(e) => update("brand", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2"
            >
              <option value="">Seleziona marca</option>
              {BRANDS.filter((b) => b !== "Tutte").map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-400">Modello *</label>
            <input
              required
              type="text"
              placeholder="Es. Golf 1.6 TDI"
              value={form.model}
              onChange={(e) => update("model", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white placeholder:text-slate-600 outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Anno *</label>
            <input
              required
              type="number"
              min={1990}
              max={2026}
              value={form.year}
              onChange={(e) => update("year", Number(e.target.value))}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">
              Prezzo (€) *
            </label>
            <input
              required
              type="number"
              min={500}
              value={form.price}
              onChange={(e) => update("price", Number(e.target.value))}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Chilometri *</label>
            <input
              required
              type="number"
              min={0}
              value={form.mileage}
              onChange={(e) => update("mileage", Number(e.target.value))}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Potenza (CV)</label>
            <input
              type="number"
              min={50}
              value={form.power}
              onChange={(e) => update("power", Number(e.target.value))}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Alimentazione</label>
            <select
              value={form.fuel}
              onChange={(e) => update("fuel", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none"
            >
              {["Benzina", "Diesel", "Elettrica", "Ibrida", "GPL"].map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-400">Cambio</label>
            <select
              value={form.transmission}
              onChange={(e) => update("transmission", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none"
            >
              <option value="Manuale">Manuale</option>
              <option value="Automatico">Automatico</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-400">Colore</label>
            <input
              type="text"
              placeholder="Es. Nero metallizzato"
              value={form.color}
              onChange={(e) => update("color", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white placeholder:text-slate-600 outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Città *</label>
            <input
              required
              type="text"
              placeholder="Es. Milano"
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white placeholder:text-slate-600 outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="text-sm text-slate-400">Descrizione *</label>
          <textarea
            required
            rows={4}
            placeholder="Descrivi lo stato dell'auto, optional, tagliandi..."
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white placeholder:text-slate-600 outline-none ring-sky-500/50 focus:ring-2"
          />
        </div>
      </div>

      <div className="rounded-2xl border border-white/5 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-white">Foto e contatti</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="text-sm text-slate-400">
              URL immagine (opzionale)
            </label>
            <div className="mt-1 flex gap-2">
              <input
                type="url"
                placeholder="https://..."
                value={form.image}
                onChange={(e) => update("image", e.target.value)}
                className="flex-1 rounded-xl bg-slate-950/60 px-4 py-3 text-white placeholder:text-slate-600 outline-none ring-sky-500/50 focus:ring-2"
              />
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
              <Upload className="h-4 w-4" />
              Incolla un link a un&apos;immagine online della tua auto
            </div>
            {(form.image || defaultImage) && (
              <img
                src={form.image || defaultImage}
                alt="Anteprima"
                className="mt-4 h-40 w-full rounded-xl object-cover"
              />
            )}
          </div>
          <div>
            <label className="text-sm text-slate-400">Il tuo nome *</label>
            <input
              required
              type="text"
              value={form.seller}
              onChange={(e) => update("seller", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Telefono *</label>
            <input
              required
              type="tel"
              placeholder="+39 333 123 4567"
              value={form.phone}
              onChange={(e) => update("phone", e.target.value)}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-3 text-white placeholder:text-slate-600 outline-none ring-sky-500/50 focus:ring-2"
            />
          </div>
        </div>
      </div>

      <button
        type="submit"
        className="w-full rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-sky-500/25 transition-all hover:brightness-110"
      >
        Pubblica annuncio gratis
      </button>
    </form>
  );
}
