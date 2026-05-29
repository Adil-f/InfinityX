"use client";

import CarCard from "./CarCard";
import { Car } from "@/lib/types";

interface CarGridProps {
  cars: Car[];
  emptyMessage?: string;
}

export default function CarGrid({
  cars,
  emptyMessage = "Nessun annuncio trovato. Prova a modificare i filtri.",
}: CarGridProps) {
  if (cars.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 py-20 text-center">
        <p className="text-6xl">🚗</p>
        <p className="mt-4 text-lg text-slate-400">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {cars.map((car, i) => (
        <CarCard key={car.id} car={car} index={i} />
      ))}
    </div>
  );
}
