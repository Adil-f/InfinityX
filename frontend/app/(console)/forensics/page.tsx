"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="forensics" title="Digital Forensics" lede="Local SHA-256, SHA-1, and MD5. Content is not stored and is not sent to a provider." placeholder="" phone={false} consent={false} forensics={true} />
    </Suspense>
  );
}
