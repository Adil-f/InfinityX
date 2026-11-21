"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="ip" title="IP" lede="Reverse DNS, Team Cymru ASN, and RIPEstat. Country is network registration, not a device location." placeholder="8.8.8.8" phone={false} consent={false} forensics={false} />
    </Suspense>
  );
}
