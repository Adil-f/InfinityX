import { Car } from "./types";
import { sampleCars } from "./data";

const STORAGE_KEY = "autovendita_cars";

export function loadCars(): Car[] {
  if (typeof window === "undefined") return sampleCars;

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sampleCars));
      return sampleCars;
    }
    const parsed = JSON.parse(stored) as Car[];
    return parsed.length > 0 ? parsed : sampleCars;
  } catch {
    return sampleCars;
  }
}

export function saveCars(cars: Car[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cars));
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
}
