"use client";

import { CarsProvider } from "@/context/CarsContext";
import CarDetailModal from "@/components/CarDetailModal";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <CarsProvider>
      {children}
      <CarDetailModal />
    </CarsProvider>
  );
}
