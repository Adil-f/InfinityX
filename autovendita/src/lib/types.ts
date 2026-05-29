export type FuelType = "Benzina" | "Diesel" | "Elettrica" | "Ibrida" | "GPL";
export type Transmission = "Manuale" | "Automatico";

export interface Car {
  id: string;
  brand: string;
  model: string;
  year: number;
  price: number;
  mileage: number;
  fuel: FuelType;
  transmission: Transmission;
  power: number;
  color: string;
  location: string;
  description: string;
  image: string;
  images: string[];
  seller: string;
  phone: string;
  featured?: boolean;
  createdAt: string;
}

export interface CarFilters {
  search: string;
  brand: string;
  fuel: string;
  minPrice: number;
  maxPrice: number;
  minYear: number;
  maxYear: number;
  transmission: string;
  sort: "recent" | "price-asc" | "price-desc" | "mileage";
}

export const defaultFilters: CarFilters = {
  search: "",
  brand: "",
  fuel: "",
  minPrice: 0,
  maxPrice: 200000,
  minYear: 2000,
  maxYear: new Date().getFullYear(),
  transmission: "",
  sort: "recent",
};
