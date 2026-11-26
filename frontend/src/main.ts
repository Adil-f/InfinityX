import "./styles.css";

type AccountInfo = {
  ig_user_id: string;
  username: string | null;
  name: string | null;
  account_type: string | null;
  permissions: string[];
  connected_at: string | null;
  token_expires_at: string | null;
};

type ConnectionStatus = {
  connected: boolean;
  account: AccountInfo | null;
  meta_configured: boolean;
  message: string | null;
};

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) {
  throw new Error("#app missing");
}

/** Local APP_API_TOKEN — same value as backend env. Not a Meta Instagram token. */
const APP_API_TOKEN = (import.meta.env.VITE_APP_API_TOKEN as string | undefined)?.trim() ?? "";

function authHeaders(): HeadersInit {
  if (!APP_API_TOKEN) {
    return {};
  }
  return { Authorization: `Bearer ${APP_API_TOKEN}` };
}

function qsFlag(name: string): string | null {
  return new URLSearchParams(window.location.search).get(name);
}

async function fetchConnection(): Promise<ConnectionStatus> {
  if (!APP_API_TOKEN) {
    throw new Error("Set VITE_APP_API_TOKEN to match backend APP_API_TOKEN.");
  }
  const res = await fetch("/api/instagram/connection", { headers: authHeaders() });
  if (res.status === 401) {
    throw new Error("Unauthorized — APP_API_TOKEN / VITE_APP_API_TOKEN mismatch.");
  }
  if (!res.ok) {
    throw new Error(`Status request failed (${res.status})`);
  }
  return (await res.json()) as ConnectionStatus;
}

function render(status: ConnectionStatus, flash: { kind: "ok" | "err"; text: string } | null) {
  const connected = status.connected && status.account;
  const account = status.account;

  app!.innerHTML = `
    <main class="shell">
      <header class="brand">
        <p class="mark">InfinityX</p>
        <h1>Instagram Creator connection</h1>
        <p class="lede">
          Official Meta Business Login for Instagram only. This page never invents
          engagement or shows a connected account until OAuth succeeds.
        </p>
      </header>

      ${
        flash
          ? `<p class="flash flash-${flash.kind}" role="status">${escapeHtml(flash.text)}</p>`
          : ""
      }

      <section class="status-panel" aria-live="polite">
        <p class="status-label">Connection status</p>
        <p class="status-value ${connected ? "is-on" : "is-off"}">
          ${connected ? "Connected" : "Not connected"}
        </p>
        ${
          connected && account
            ? `<dl class="facts">
                <div><dt>Username</dt><dd>@${escapeHtml(account.username ?? "—")}</dd></div>
                <div><dt>Account type</dt><dd>${escapeHtml(account.account_type ?? "—")}</dd></div>
                <div><dt>Instagram user ID</dt><dd>${escapeHtml(account.ig_user_id)}</dd></div>
                <div><dt>Granted permissions</dt><dd>${escapeHtml(account.permissions.join(", ") || "—")}</dd></div>
                <div><dt>Token expires</dt><dd>${escapeHtml(account.token_expires_at ?? "—")}</dd></div>
              </dl>`
            : `<p class="hint">${escapeHtml(status.message ?? "Complete Meta OAuth to connect.")}</p>`
        }
      </section>

      <div class="actions">
        ${
          connected
            ? `<button type="button" class="btn ghost" id="disconnect">Disconnect</button>`
            : `<a class="btn primary" href="/api/oauth/instagram/start">Connect with Instagram</a>`
        }
        ${
          !status.meta_configured
            ? `<p class="warn">Meta App ID / secret / redirect URI are not configured on the server yet.</p>`
            : ""
        }
      </div>
    </main>
  `;

  const disconnect = document.querySelector<HTMLButtonElement>("#disconnect");
  disconnect?.addEventListener("click", async () => {
    const res = await fetch("/api/instagram/connection", {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) {
      render(status, {
        kind: "err",
        text: res.status === 401 ? "Unauthorized disconnect." : `Disconnect failed (${res.status})`,
      });
      return;
    }
    window.history.replaceState({}, "", "/");
    const next = await fetchConnection();
    render(next, { kind: "ok", text: "Connection cleared." });
  });
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function boot() {
  let flash: { kind: "ok" | "err"; text: string } | null = null;
  const connectedParam = qsFlag("connected");
  const err = qsFlag("error_description") || qsFlag("error");
  if (connectedParam === "true") {
    flash = { kind: "ok", text: "OAuth completed. Showing status from stored tokens." };
  } else if (err) {
    flash = { kind: "err", text: err };
  }

  try {
    const status = await fetchConnection();
    render(status, flash);
  } catch (e) {
    render(
      {
        connected: false,
        account: null,
        meta_configured: false,
        message: "Backend unreachable. Start the FastAPI server on port 8000.",
      },
      { kind: "err", text: e instanceof Error ? e.message : "Failed to load status" },
    );
  }
}

void boot();
