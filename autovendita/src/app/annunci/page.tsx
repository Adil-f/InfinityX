"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import Filters from "@/components/Filters";
import CarGrid from "@/components/CarGrid";
import { useCars } from "@/context/CarsContext";

function AnnunciContent() {
  const searchParams = useSearchParams();
  const { filteredCars, setFilters, isLoading } = useCars();

  useEffect(() => {
    const q = searchParams.get("q");
    const brand = searchParams.get("brand");
    if (q) setFilters({ search: q });
    if (brand) setFilters({ brand });
  }, [searchParams, setFilters]);

  return (
    <>
      <Filters />
      {isLoading ? (
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-72 animate-pulse rounded-2xl bg-slate-800/50"
            />
          ))}
        </div>
      ) : (
        <div className="mt-10">
          <CarGrid cars={filteredCars} />
        </div>
      )}
    </>
  );
}

export default function AnnunciPage() {
  return (
    <div className="pt-28 pb-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-white sm:text-4xl">
            Tutti gli annunci
          </h1>
          <p className="mt-2 text-slate-400">
            Esplora le auto in vendita e trova quella perfetta per te
          </p>
        </div>

        <Suspense
          fallback={
            <div className="h-40 animate-pulse rounded-2xl bg-slate-800/50" />
          }
        >
          <AnnunciContent />
        </Suspense>
      </div>
    </div>
  );
}
