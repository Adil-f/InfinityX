"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="phone" title="Phone" lede="International formatting for Pakistan, Italy, and other numbering plans. No subscriber name is requested or returned." placeholder="+393331234567" phone={true} consent={false} forensics={false} />
    </Suspense>
  );
}
