"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="cnic" title="CNIC" lede="Pakistani CNIC format validation, consent, and an authorized-provider connector. NADRA is not queried." placeholder="35202-1234567-1" phone={false} consent={true} forensics={false} />
    </Suspense>
  );
}
