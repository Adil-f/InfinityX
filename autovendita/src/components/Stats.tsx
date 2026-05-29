"use client";

import { motion } from "framer-motion";
import { Car, TrendingUp, Users, Clock } from "lucide-react";

const stats = [
  { icon: Car, value: "2.500+", label: "Auto in vendita" },
  { icon: Users, value: "15.000+", label: "Utenti attivi" },
  { icon: TrendingUp, value: "98%", label: "Soddisfazione" },
  { icon: Clock, value: "24h", label: "Tempo medio vendita" },
];

export default function Stats() {
  return (
    <section className="py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="group rounded-2xl border border-white/5 bg-white/[0.02] p-6 text-center transition-colors hover:border-sky-500/20 hover:bg-sky-500/5"
            >
              <stat.icon className="mx-auto h-8 w-8 text-sky-400 transition-transform group-hover:scale-110" />
              <p className="mt-3 text-3xl font-bold text-white">{stat.value}</p>
              <p className="mt-1 text-sm text-slate-400">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
