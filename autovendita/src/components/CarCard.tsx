"use client";

import { motion } from "framer-motion";
import { Calendar, Fuel, Gauge, MapPin, Settings2 } from "lucide-react";
import { Car } from "@/lib/types";
import { formatMileage, formatPrice } from "@/lib/data";
import { useCars } from "@/context/CarsContext";

interface CarCardProps {
  car: Car;
  index?: number;
}

export default function CarCard({ car, index = 0 }: CarCardProps) {
  const { selectCar } = useCars();

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -4 }}
      onClick={() => selectCar(car)}
      className="group cursor-pointer overflow-hidden rounded-2xl border border-white/5 bg-slate-900/50 transition-all hover:border-sky-500/30 hover:shadow-xl hover:shadow-sky-500/5"
    >
      <div className="relative aspect-[16/10] overflow-hidden">
        <img
          src={car.image}
          alt={`${car.brand} ${car.model}`}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        {car.featured && (
          <span className="absolute top-3 left-3 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 px-3 py-1 text-xs font-bold text-white shadow-lg">
            In evidenza
          </span>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      </div>

      <div className="p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-white group-hover:text-sky-400 transition-colors">
              {car.brand} {car.model}
            </h3>
            <p className="mt-0.5 flex items-center gap-1 text-sm text-slate-400">
              <MapPin className="h-3.5 w-3.5" />
              {car.location}
            </p>
          </div>
          <p className="text-xl font-bold text-sky-400 whitespace-nowrap">
            {formatPrice(car.price)}
          </p>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2">
          {[
            { icon: Calendar, value: car.year },
            { icon: Gauge, value: formatMileage(car.mileage) },
            { icon: Fuel, value: car.fuel },
            { icon: Settings2, value: car.transmission },
          ].map(({ icon: Icon, value }) => (
            <div
              key={String(value)}
              className="flex items-center gap-2 rounded-lg bg-white/[0.03] px-3 py-2 text-xs text-slate-400"
            >
              <Icon className="h-3.5 w-3.5 text-sky-400/70" />
              {value}
            </div>
          ))}
        </div>
      </div>
    </motion.article>
  );
}
