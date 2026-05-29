"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { sampleCars } from "@/lib/data";
import { generateId, loadCars, saveCars } from "@/lib/storage";
import { Car, CarFilters, defaultFilters } from "@/lib/types";

interface CarsContextValue {
  cars: Car[];
  filters: CarFilters;
  filteredCars: Car[];
  selectedCar: Car | null;
  isLoading: boolean;
  setFilters: (filters: Partial<CarFilters>) => void;
  resetFilters: () => void;
  addCar: (car: Omit<Car, "id" | "createdAt">) => void;
  deleteCar: (id: string) => void;
  selectCar: (car: Car | null) => void;
  featuredCars: Car[];
}

const CarsContext = createContext<CarsContextValue | null>(null);

function filterAndSort(cars: Car[], filters: CarFilters): Car[] {
  let result = cars.filter((car) => {
    const searchLower = filters.search.toLowerCase();
    const matchesSearch =
      !filters.search ||
      `${car.brand} ${car.model} ${car.location} ${car.color}`
        .toLowerCase()
        .includes(searchLower);

    const matchesBrand =
      !filters.brand || filters.brand === "Tutte" || car.brand === filters.brand;
    const matchesFuel = !filters.fuel || car.fuel === filters.fuel;
    const matchesTransmission =
      !filters.transmission || car.transmission === filters.transmission;
    const matchesPrice =
      car.price >= filters.minPrice && car.price <= filters.maxPrice;
    const matchesYear =
      car.year >= filters.minYear && car.year <= filters.maxYear;

    return (
      matchesSearch &&
      matchesBrand &&
      matchesFuel &&
      matchesTransmission &&
      matchesPrice &&
      matchesYear
    );
  });

  switch (filters.sort) {
    case "price-asc":
      result = [...result].sort((a, b) => a.price - b.price);
      break;
    case "price-desc":
      result = [...result].sort((a, b) => b.price - a.price);
      break;
    case "mileage":
      result = [...result].sort((a, b) => a.mileage - b.mileage);
      break;
    default:
      result = [...result].sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
  }

  return result;
}

export function CarsProvider({ children }: { children: React.ReactNode }) {
  const [cars, setCars] = useState<Car[]>(sampleCars);
  const [filters, setFiltersState] = useState<CarFilters>(defaultFilters);
  const [selectedCar, setSelectedCar] = useState<Car | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setCars(loadCars());
    setIsLoading(false);
  }, []);

  const persist = useCallback((updated: Car[]) => {
    setCars(updated);
    saveCars(updated);
  }, []);

  const setFilters = useCallback((partial: Partial<CarFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...partial }));
  }, []);

  const resetFilters = useCallback(() => {
    setFiltersState(defaultFilters);
  }, []);

  const addCar = useCallback(
    (carData: Omit<Car, "id" | "createdAt">) => {
      const newCar: Car = {
        ...carData,
        id: generateId(),
        createdAt: new Date().toISOString(),
      };
      persist([newCar, ...cars]);
    },
    [cars, persist]
  );

  const deleteCar = useCallback(
    (id: string) => {
      persist(cars.filter((c) => c.id !== id));
      setSelectedCar(null);
    },
    [cars, persist]
  );

  const filteredCars = useMemo(
    () => filterAndSort(cars, filters),
    [cars, filters]
  );

  const featuredCars = useMemo(
    () => cars.filter((c) => c.featured).slice(0, 4),
    [cars]
  );

  return (
    <CarsContext.Provider
      value={{
        cars,
        filters,
        filteredCars,
        selectedCar,
        isLoading,
        setFilters,
        resetFilters,
        addCar,
        deleteCar,
        selectCar: setSelectedCar,
        featuredCars,
      }}
    >
      {children}
    </CarsContext.Provider>
  );
}

export function useCars() {
  const ctx = useContext(CarsContext);
  if (!ctx) throw new Error("useCars must be used within CarsProvider");
  return ctx;
}
