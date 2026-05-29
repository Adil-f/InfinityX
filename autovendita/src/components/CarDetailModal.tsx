"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  Calendar,
  Fuel,
  Gauge,
  MapPin,
  Phone,
  Settings2,
  User,
  X,
  Zap,
  Palette,
} from "lucide-react";
import { useCars } from "@/context/CarsContext";
import { formatMileage, formatPrice } from "@/lib/data";

export default function CarDetailModal() {
  const { selectedCar, selectCar } = useCars();

  return (
    <AnimatePresence>
      {selectedCar && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => selectCar(null)}
            className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-4 z-[70] mx-auto flex max-h-[90vh] max-w-3xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-900 shadow-2xl sm:inset-auto sm:top-1/2 sm:left-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-full"
          >
            <div className="relative aspect-[16/9] shrink-0 overflow-hidden">
              <img
                src={selectedCar.image}
                alt={`${selectedCar.brand} ${selectedCar.model}`}
                className="h-full w-full object-cover"
              />
              <button
                onClick={() => selectCar(null)}
                className="absolute top-4 right-4 rounded-full bg-slate-900/80 p-2 text-white backdrop-blur-sm transition-colors hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
              {selectedCar.featured && (
                <span className="absolute top-4 left-4 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 px-3 py-1 text-xs font-bold text-white">
                  In evidenza
                </span>
              )}
            </div>

            <div className="overflow-y-auto p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    {selectedCar.brand} {selectedCar.model}
                  </h2>
                  <p className="mt-1 flex items-center gap-1 text-slate-400">
                    <MapPin className="h-4 w-4" />
                    {selectedCar.location}
                  </p>
                </div>
                <p className="text-3xl font-bold text-sky-400">
                  {formatPrice(selectedCar.price)}
                </p>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { icon: Calendar, label: "Anno", value: selectedCar.year },
                  {
                    icon: Gauge,
                    label: "Chilometri",
                    value: formatMileage(selectedCar.mileage),
                  },
                  { icon: Fuel, label: "Carburante", value: selectedCar.fuel },
                  {
                    icon: Settings2,
                    label: "Cambio",
                    value: selectedCar.transmission,
                  },
                  {
                    icon: Zap,
                    label: "Potenza",
                    value: `${selectedCar.power} CV`,
                  },
                  {
                    icon: Palette,
                    label: "Colore",
                    value: selectedCar.color,
                  },
                ].map(({ icon: Icon, label, value }) => (
                  <div
                    key={label}
                    className="rounded-xl bg-white/[0.03] p-3 text-center"
                  >
                    <Icon className="mx-auto h-5 w-5 text-sky-400" />
                    <p className="mt-1 text-xs text-slate-500">{label}</p>
                    <p className="text-sm font-medium text-white">{value}</p>
                  </div>
                ))}
              </div>

              <div className="mt-6">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Descrizione
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">
                  {selectedCar.description}
                </p>
              </div>

              <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-white/5 bg-white/[0.02] p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sky-500/10">
                    <User className="h-6 w-6 text-sky-400" />
                  </div>
                  <div>
                    <p className="font-medium text-white">{selectedCar.seller}</p>
                    <p className="text-sm text-slate-400">Venditore privato</p>
                  </div>
                </div>
                <a
                  href={`tel:${selectedCar.phone.replace(/\s/g, "")}`}
                  className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-6 py-3 font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:brightness-110"
                >
                  <Phone className="h-5 w-5" />
                  Contatta venditore
                </a>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
