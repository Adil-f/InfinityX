import SellCarForm from "@/components/SellCarForm";
import { Camera, Clock, Euro } from "lucide-react";

const benefits = [
  {
    icon: Euro,
    title: "Completamente gratis",
    description: "Nessun costo per pubblicare il tuo annuncio",
  },
  {
    icon: Clock,
    title: "Online in 3 minuti",
    description: "Compila il form e il tuo annuncio è subito visibile",
  },
  {
    icon: Camera,
    title: "Aggiungi le foto",
    description: "Mostra la tua auto al meglio con immagini di qualità",
  },
];

export default function VendiPage() {
  return (
    <div className="pt-28 pb-20">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white sm:text-4xl">
            Vendi la tua auto
          </h1>
          <p className="mt-3 text-slate-400">
            Compila il modulo e raggiungi migliaia di potenziali acquirenti
          </p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {benefits.map((b) => (
            <div
              key={b.title}
              className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 text-center"
            >
              <b.icon className="mx-auto h-8 w-8 text-sky-400" />
              <h3 className="mt-2 text-sm font-semibold text-white">
                {b.title}
              </h3>
              <p className="mt-1 text-xs text-slate-400">{b.description}</p>
            </div>
          ))}
        </div>

        <div className="mt-10">
          <SellCarForm />
        </div>
      </div>
    </div>
  );
}
