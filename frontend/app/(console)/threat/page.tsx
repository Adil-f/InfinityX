"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="threat" title="Threat" lede="URLhaus for a host, plus VirusTotal and OTX when keys exist. The submitted URL is not fetched." placeholder="example.com" phone={false} consent={false} forensics={false} />
    </Suspense>
  );
}
