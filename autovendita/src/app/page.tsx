import Hero from "@/components/Hero";
import Stats from "@/components/Stats";
import FeaturedCars from "@/components/FeaturedCars";
import HowItWorks from "@/components/HowItWorks";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Stats />
      <FeaturedCars />
      <HowItWorks />

      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl border border-sky-500/20 bg-gradient-to-br from-sky-950/50 to-blue-950/30 p-10 sm:p-16">
            <div className="absolute top-0 right-0 h-64 w-64 rounded-full bg-sky-500/10 blur-3xl" />
            <div className="relative">
              <h2 className="text-3xl font-bold text-white sm:text-4xl">
                Pronto a vendere la tua auto?
              </h2>
              <p className="mt-4 max-w-lg text-slate-400">
                Pubblica il tuo annuncio in pochi minuti, completamente gratis.
                Raggiungi migliaia di acquirenti in tutta Italia.
              </p>
              <Link
                href="/vendi"
                className="mt-8 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-8 py-4 font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:brightness-110"
              >
                Inizia ora
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
