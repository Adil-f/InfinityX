"use client";
import { Suspense } from "react";
import { ModuleScreen } from "@/components/ModuleScreen";
export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ModuleScreen module="username" title="Username" lede="Public GitHub and GitLab profiles, plus URL templates that are not existence checks." placeholder="octocat" phone={false} consent={false} forensics={false} />
    </Suspense>
  );
}
