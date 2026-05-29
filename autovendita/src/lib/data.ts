import { Car } from "./types";

export const BRANDS = [
  "Tutte",
  "Audi",
  "BMW",
  "Fiat",
  "Ford",
  "Mercedes",
  "Peugeot",
  "Renault",
  "Tesla",
  "Toyota",
  "Volkswagen",
];

export const sampleCars: Car[] = [
  {
    id: "1",
    brand: "BMW",
    model: "Serie 3 320d",
    year: 2021,
    price: 32900,
    mileage: 45000,
    fuel: "Diesel",
    transmission: "Automatico",
    power: 190,
    color: "Nero",
    location: "Milano",
    description:
      "BMW Serie 3 in condizioni impeccabili. Full optional, interni in pelle, navigatore, sensori di parcheggio e cruise control adattivo. Un solo proprietario, tagliandi regolari in officina autorizzata.",
    image:
      "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800&q=80",
      "https://images.unsplash.com/photo-1617531653332-bd46c24f2068?w=800&q=80",
    ],
    seller: "Marco R.",
    phone: "+39 333 123 4567",
    featured: true,
    createdAt: "2026-05-20T10:00:00Z",
  },
  {
    id: "2",
    brand: "Fiat",
    model: "500e Icon",
    year: 2023,
    price: 21500,
    mileage: 12000,
    fuel: "Elettrica",
    transmission: "Automatico",
    power: 118,
    color: "Bianco",
    location: "Roma",
    description:
      "Fiat 500e perfetta per la città. Autonomia fino a 320 km, ricarica rapida, design iconico. Garanzia residua, parcheggio agevolato e accesso ZTL.",
    image:
      "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&q=80",
    ],
    seller: "Giulia B.",
    phone: "+39 347 987 6543",
    featured: true,
    createdAt: "2026-05-18T14:30:00Z",
  },
  {
    id: "3",
    brand: "Mercedes",
    model: "Classe A 180",
    year: 2022,
    price: 28900,
    mileage: 28000,
    fuel: "Benzina",
    transmission: "Automatico",
    power: 136,
    color: "Grigio",
    location: "Torino",
    description:
      "Mercedes Classe A con pacchetto AMG Line. MBUX, fari LED, telecamera posteriore. Auto sempre tenuta in garage, nessun incidente.",
    image:
      "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=800&q=80",
    ],
    seller: "Luca M.",
    phone: "+39 320 555 7890",
    featured: true,
    createdAt: "2026-05-15T09:00:00Z",
  },
  {
    id: "4",
    brand: "Volkswagen",
    model: "Golf 8 GTI",
    year: 2020,
    price: 26500,
    mileage: 62000,
    fuel: "Benzina",
    transmission: "Manuale",
    power: 245,
    color: "Rosso",
    location: "Bologna",
    description:
      "Golf GTI MK8, il mito continua. 245 CV, soundaktor, sedili sportivi, cerchi da 18\". Perfetta per chi ama guidare.",
    image:
      "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800&q=80",
    ],
    seller: "Andrea P.",
    phone: "+39 338 222 3333",
    featured: false,
    createdAt: "2026-05-12T16:00:00Z",
  },
  {
    id: "5",
    brand: "Tesla",
    model: "Model 3 Long Range",
    year: 2023,
    price: 38900,
    mileage: 18000,
    fuel: "Elettrica",
    transmission: "Automatico",
    power: 366,
    color: "Blu",
    location: "Firenze",
    description:
      "Tesla Model 3 Long Range con Autopilot. Autonomia 580 km, supercharger incluso per 6 mesi. Interni premium, vetri oscurati.",
    image:
      "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=800&q=80",
    ],
    seller: "Elena S.",
    phone: "+39 349 111 2222",
    featured: true,
    createdAt: "2026-05-10T11:00:00Z",
  },
  {
    id: "6",
    brand: "Audi",
    model: "A4 Avant",
    year: 2019,
    price: 24800,
    mileage: 78000,
    fuel: "Diesel",
    transmission: "Automatico",
    power: 150,
    color: "Nero",
    location: "Napoli",
    description:
      "Audi A4 Avant quattro, ideale per famiglie. Virtual cockpit, clima bizona, gancio traino. Revisione appena fatta.",
    image:
      "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800&q=80",
    ],
    seller: "Francesco D.",
    phone: "+39 335 444 5555",
    featured: false,
    createdAt: "2026-05-08T08:00:00Z",
  },
  {
    id: "7",
    brand: "Toyota",
    model: "RAV4 Hybrid",
    year: 2022,
    price: 31500,
    mileage: 35000,
    fuel: "Ibrida",
    transmission: "Automatico",
    power: 218,
    color: "Verde",
    location: "Verona",
    description:
      "Toyota RAV4 Hybrid AWD. Consumi ridotti, spazio generoso, sicurezza Toyota Safety Sense. Perfetta per ogni avventura.",
    image:
      "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=800&q=80",
    ],
    seller: "Sara T.",
    phone: "+39 340 666 7777",
    featured: false,
    createdAt: "2026-05-05T13:00:00Z",
  },
  {
    id: "8",
    brand: "Peugeot",
    model: "208 GT",
    year: 2021,
    price: 17200,
    mileage: 41000,
    fuel: "Benzina",
    transmission: "Manuale",
    power: 130,
    color: "Giallo",
    location: "Palermo",
    description:
      "Peugeot 208 GT con i-Cockpit 3D. Compatta, agile e piena di stile. Ottima per giovani e città.",
    image:
      "https://images.unsplash.com/photo-1609521263047-f8f205293bb4?w=800&q=80",
    images: [
      "https://images.unsplash.com/photo-1609521263047-f8f205293bb4?w=800&q=80",
    ],
    seller: "Antonio L.",
    phone: "+39 328 888 9999",
    featured: false,
    createdAt: "2026-05-01T10:00:00Z",
  },
];

export function formatPrice(price: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(price);
}

export function formatMileage(km: number): string {
  return new Intl.NumberFormat("it-IT").format(km) + " km";
}
