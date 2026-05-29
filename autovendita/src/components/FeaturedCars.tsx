"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { useCars } from "@/context/CarsContext";
import CarGrid from "./CarGrid";

export default function FeaturedCars() {
  const { featuredCars } = useCars();

  return (
    <section className="py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold text-white sm:text-4xl">
              Auto in evidenza
            </h2>
            <p className="mt-2 text-slate-400">
              Le migliori offerte selezionate per te
            </p>
          </motion.div>
          <Link
            href="/annunci"
            className="hidden items-center gap-2 text-sm font-medium text-sky-400 transition-colors hover:text-sky-300 sm:flex"
          >
            Vedi tutti
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="mt-10">
          <CarGrid cars={featuredCars} />
        </div>

        <div className="mt-8 text-center sm:hidden">
          <Link
            href="/annunci"
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-6 py-3 text-sm font-medium text-white"
          >
            Vedi tutti gli annunci
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
