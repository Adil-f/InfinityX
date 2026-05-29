"use client";

import { Search, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";
import { useCars } from "@/context/CarsContext";
import { BRANDS } from "@/lib/data";
import { formatPrice } from "@/lib/data";

export default function Filters() {
  const { filters, setFilters, resetFilters, filteredCars } = useCars();
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/50 p-5 backdrop-blur-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Cerca marca, modello, città..."
            value={filters.search}
            onChange={(e) => setFilters({ search: e.target.value })}
            className="w-full rounded-xl bg-slate-950/60 py-3 pl-12 pr-4 text-white placeholder:text-slate-500 outline-none ring-sky-500/50 focus:ring-2"
          />
        </div>

        <select
          value={filters.brand}
          onChange={(e) => setFilters({ brand: e.target.value })}
          className="rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2 lg:w-40"
        >
          <option value="">Tutte le marche</option>
          {BRANDS.filter((b) => b !== "Tutte").map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>

        <select
          value={filters.sort}
          onChange={(e) =>
            setFilters({
              sort: e.target.value as typeof filters.sort,
            })
          }
          className="rounded-xl bg-slate-950/60 px-4 py-3 text-white outline-none ring-sky-500/50 focus:ring-2 lg:w-44"
        >
          <option value="recent">Più recenti</option>
          <option value="price-asc">Prezzo crescente</option>
          <option value="price-desc">Prezzo decrescente</option>
          <option value="mileage">Chilometri</option>
        </select>

        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filtri avanzati
        </button>
      </div>

      {showAdvanced && (
        <div className="mt-4 grid gap-4 border-t border-white/5 pt-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="text-xs font-medium text-slate-400">
              Alimentazione
            </label>
            <select
              value={filters.fuel}
              onChange={(e) => setFilters({ fuel: e.target.value })}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-2.5 text-sm text-white outline-none"
            >
              <option value="">Tutte</option>
              {["Benzina", "Diesel", "Elettrica", "Ibrida", "GPL"].map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400">
              Cambio
            </label>
            <select
              value={filters.transmission}
              onChange={(e) => setFilters({ transmission: e.target.value })}
              className="mt-1 w-full rounded-xl bg-slate-950/60 px-4 py-2.5 text-sm text-white outline-none"
            >
              <option value="">Tutti</option>
              <option value="Manuale">Manuale</option>
              <option value="Automatico">Automatico</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400">
              Prezzo max: {formatPrice(filters.maxPrice)}
            </label>
            <input
              type="range"
              min={5000}
              max={100000}
              step={1000}
              value={filters.maxPrice}
              onChange={(e) =>
                setFilters({ maxPrice: Number(e.target.value) })
              }
              className="mt-2 w-full accent-sky-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400">
              Anno min: {filters.minYear}
            </label>
            <input
              type="range"
              min={2000}
              max={2026}
              value={filters.minYear}
              onChange={(e) =>
                setFilters({ minYear: Number(e.target.value) })
              }
              className="mt-2 w-full accent-sky-500"
            />
          </div>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between">
        <p className="text-sm text-slate-400">
          <span className="font-semibold text-white">{filteredCars.length}</span>{" "}
          annunci trovati
        </p>
        {(filters.search ||
          filters.brand ||
          filters.fuel ||
          filters.transmission) && (
          <button
            onClick={resetFilters}
            className="flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300"
          >
            <X className="h-4 w-4" />
            Reset filtri
          </button>
        )}
      </div>
    </div>
  );
}
