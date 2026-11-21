"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="domain" title="Domain" lede="DNS, RDAP, and certificate transparency for a domain name." placeholder="example.com" phone={false} consent={false} forensics={false} />
    </Suspense>
  );
}
