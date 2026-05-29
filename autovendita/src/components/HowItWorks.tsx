"use client";

import { motion } from "framer-motion";
import { Camera, MessageCircle, Search, PenLine } from "lucide-react";

const steps = [
  {
    icon: PenLine,
    title: "Crea l'annuncio",
    description:
      "Inserisci marca, modello, chilometri e foto. Ci vogliono solo 3 minuti.",
  },
  {
    icon: Camera,
    title: "Aggiungi le foto",
    description:
      "Le auto con foto di qualità ricevono 5 volte più contatti.",
  },
  {
    icon: Search,
    title: "Raggiungi acquirenti",
    description:
      "Il tuo annuncio appare subito nelle ricerche di migliaia di utenti.",
  },
  {
    icon: MessageCircle,
    title: "Vendi e concludi",
    description:
      "Ricevi messaggi diretti, organizza un test drive e chiudi l'affare.",
  },
];

export default function HowItWorks() {
  return (
    <section className="py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Come funziona
          </h2>
          <p className="mt-4 text-slate-400">
            Vendere la tua auto non è mai stato così semplice
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="relative rounded-2xl border border-white/5 bg-gradient-to-b from-white/[0.04] to-transparent p-6"
            >
              <span className="absolute -top-3 left-6 rounded-full bg-sky-500 px-3 py-0.5 text-xs font-bold text-white">
                {i + 1}
              </span>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-500/10">
                <step.icon className="h-6 w-6 text-sky-400" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-white">
                {step.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
