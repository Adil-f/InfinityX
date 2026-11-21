"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="social" title="Social" lede="The same public profile checks as Username. Templates are labeled unverified." placeholder="github" phone={false} consent={false} forensics={false} />
    </Suspense>
  );
}
