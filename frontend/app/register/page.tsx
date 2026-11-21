"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", organization: "", accept_terms: false });
  const [error, setError] = useState("");

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const body = await api<{ access_token: string }>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(form) });
      sessionStorage.setItem("ix_token", body.access_token);
      router.push("/overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the organization");
    }
  }

  return (
    <main className="auth-screen">
      <form className="card auth-card" onSubmit={submit}>
        <h1>Create an organization</h1>
        <label>Organization<input value={form.organization} onChange={(event) => set("organization", event.target.value)} required /></label>
        <label>Your name<input value={form.full_name} onChange={(event) => set("full_name", event.target.value)} required /></label>
        <label>Email<input type="email" value={form.email} onChange={(event) => set("email", event.target.value)} required /></label>
        <label>Password<input type="password" value={form.password} onChange={(event) => set("password", event.target.value)} required /></label>
        <label className="check"><input type="checkbox" checked={form.accept_terms} onChange={(event) => set("accept_terms", event.target.checked)} /> I will use Infinity X only for authorized investigations of public or licensed sources.</label>
        {error && <div className="error">{error}</div>}
        <button className="btn" type="submit">Create</button>
        <p><Link href="/login">Already have an account</Link></p>
      </form>
    </main>
  );
}
