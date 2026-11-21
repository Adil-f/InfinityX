"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="email" title="Email" lede="Syntax, public DNS authentication, Gravatar existence, and HIBP only when a key is configured." placeholder="analyst@example.com" phone={false} consent={false} forensics={false} />
    </Suspense>
  );
}
