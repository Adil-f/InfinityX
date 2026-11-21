"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return <Suspense fallback={<p>Loading…</p>}><ModuleScreen title="Universal Search" lede="Route one indicator to the modules that can answer it from public sources. A 13-digit number is not guessed." placeholder="example.com, email, IP, +39…, or a hash" /></Suspense>;
}
