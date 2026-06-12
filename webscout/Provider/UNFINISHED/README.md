# UNFINISHED provider implementations.

Providers in this directory are NOT exported in
``webscout/Provider/__init__``. They live here so the source is preserved
when their upstream disappears, so anyone who wants to revive them has
a starting point, and so the live-test runner skips them.

See ``docs/UNFINISHED_PROVIDERS.md`` for the rationale for each entry.

2026-06-12: bulk move of providers whose upstreams went away:
- Ayle    (DNS NXDOMAIN, domain dead)
- Elmo    (Vercel 404, public API gone, only the Chrome extension may still work)
- SonusAI (now login-gated; same backend serves a free image gen)
- LLMChatCo (every route returns a "Redirecting..." JS shell — gated)
- Meta    (requires Facebook OAuth, code path is dead since Meta killed
            the public anonymous interface and the `mbasic.facebook.com`
            device-based login flow)
