"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SignupPage() {
  const router = useRouter();
  const [orgName, setOrgName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orgName, name, email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Signup failed");
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-10">
      <form onSubmit={onSubmit} className="card p-8 w-full max-w-sm flex flex-col gap-4">
        <h1 className="font-display text-2xl font-extrabold">Create your workspace</h1>
        <p className="text-sm text-cream/50 -mt-2">For your agency or research team.</p>
        <div className="flex flex-col gap-1">
          <label className="label">Organization name</label>
          <input className="input" required value={orgName} onChange={(e) => setOrgName(e.target.value)} placeholder="e.g. Kalahari Insights" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="label">Your name</label>
          <input className="input" required value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="label">Email</label>
          <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="label">Password</label>
          <input
            className="input"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Creating…" : "Create workspace"}
        </button>
        <p className="text-sm text-cream/50 text-center">
          Already have an account?{" "}
          <Link href="/login" className="text-teal">
            Sign in
          </Link>
        </p>
      </form>
    </main>
  );
}
