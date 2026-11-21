import Link from "next/link";

export default function HomePage() {
  return (
    <main className="landing">
      <p className="muted">INFINITY X</p>
      <h1 className="hero-mark">Global OSINT for authorized investigations.</h1>
      <p className="lede">Collect, normalize, and report from public sources and providers your organization is licensed to use. Pakistan and Italy are in scope for numbering-plan analysis. CNIC support is format validation plus an authorized provider interface.</p>
      <div className="cluster">
        <Link className="btn" href="/login">Sign in</Link>
        <Link className="btn secondary" href="/register">Create an organization</Link>
        <span className="muted">The original marketing site remains in legacy/marketing.</span>
      </div>
      <section className="grid-3" style={{ marginTop: 28 }}>
        <article className="card"><h2>Public sources</h2><p>DNS, RDAP, certificate transparency, Team Cymru, and RIPEstat run when the network allows. Failures stay failures.</p></article>
        <article className="card"><h2>No identity shopping</h2><p>Phone results are numbering-plan metadata. CNIC checks do not query NADRA. Missing provider keys are marked unavailable.</p></article>
        <article className="card"><h2>Evidence, not accusation</h2><p>The investigator separates verified observations from hypotheses and will not accuse a person of a crime.</p></article>
      </section>
    </main>
  );
}
