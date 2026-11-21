"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const body = await api<{ access_token?: string; mfa_required?: boolean; mfa_token?: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (body.mfa_required && body.mfa_token) {
        setMfaToken(body.mfa_token);
        return;
      }
      if (body.access_token) {
        sessionStorage.setItem("ix_token", body.access_token);
        router.push("/overview");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    }
  }

  async function verify(event: FormEvent) {
    event.preventDefault();
    try {
      const body = await api<{ access_token: string }>("/api/v1/auth/mfa/login", {
        method: "POST",
        body: JSON.stringify({ mfa_token: mfaToken, code }),
      });
      sessionStorage.setItem("ix_token", body.access_token);
      router.push("/overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Code rejected");
    }
  }

  return (
    <main className="auth-screen">
      <form className="card auth-card" onSubmit={mfaToken ? verify : submit}>
        <h1>Sign in</h1>
        <p className="muted">Local development can seed a fixture account. The password is only in your environment file, and search results are not fixtures.</p>
        {!mfaToken && (
          <>
            <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>
            <label>Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required /></label>
          </>
        )}
        {mfaToken && <label>Authentication code<input value={code} onChange={(event) => setCode(event.target.value)} inputMode="numeric" required /></label>}
        {error && <div className="error">{error}</div>}
        <button className="btn" type="submit">{mfaToken ? "Verify" : "Continue"}</button>
        <p><Link href="/register">Create an organization</Link></p>
      </form>
    </main>
  );
}
