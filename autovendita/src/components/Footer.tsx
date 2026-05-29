import Link from "next/link";
import { Car, Mail, MapPin, Phone } from "lucide-react";

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-white/5 bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-600">
                <Car className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">
                Auto<span className="text-sky-400">Vendita</span>
              </span>
            </div>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-400">
              Il marketplace italiano per comprare e vendere auto in modo semplice,
              sicuro e veloce. Migliaia di annunci verificati, contatto diretto
              con i venditori.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Navigazione
            </h3>
            <ul className="mt-4 space-y-3">
              {[
                { href: "/", label: "Home" },
                { href: "/annunci", label: "Tutti gli annunci" },
                { href: "/vendi", label: "Vendi la tua auto" },
              ].map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-slate-400 transition-colors hover:text-sky-400"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Contatti
            </h3>
            <ul className="mt-4 space-y-3">
              <li className="flex items-center gap-2 text-sm text-slate-400">
                <Mail className="h-4 w-4 text-sky-400" />
                info@autovendita.it
              </li>
              <li className="flex items-center gap-2 text-sm text-slate-400">
                <Phone className="h-4 w-4 text-sky-400" />
                800 123 456
              </li>
              <li className="flex items-center gap-2 text-sm text-slate-400">
                <MapPin className="h-4 w-4 text-sky-400" />
                Milano, Italia
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/5 pt-8 sm:flex-row">
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} AutoVendita. Tutti i diritti riservati.
          </p>
          <p className="text-xs text-slate-500">
            Creato con passione per gli appassionati di motori 🇮🇹
          </p>
        </div>
      </div>
    </footer>
  );
}
