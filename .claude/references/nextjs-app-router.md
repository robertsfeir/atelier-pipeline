# Next.js 14+ App Router Reference

Colby reads this when working on Next.js pages, layouts, routing, or
server/client component decisions.

---

<section id="core-mental-model">

## Core Mental Model

The App Router is server-first. Components are Server Components by default.
Client Components require explicit `"use client"` directive. Think of it as:
server renders everything, client hydrates interactive islands.

## File Conventions

| File | Purpose |
|------|---------|
| `layout.tsx` | Persistent wrapper — doesn't re-render on navigation |
| `page.tsx` | Route entry point — unique content for this URL |
| `loading.tsx` | Suspense fallback while page data loads (streaming) |
| `error.tsx` | Error boundary for this route segment |
| `not-found.tsx` | 404 for this segment |
| `route.ts` | API route handler (GET, POST, etc.) |

</section>

<section id="server-vs-client-components">

## Server vs Client Components

### Server Components (default — no directive)
- Can `async/await` directly — fetch data in the component.
- Can access server resources (DB, filesystem, env vars).
- Zero JS shipped to the client for these components.
- Cannot use hooks (`useState`, `useEffect`, etc.).
- Cannot use browser APIs (`window`, `document`, `localStorage`).
- Cannot use event handlers (`onClick`, `onChange`, etc.).

### Client Components (`"use client"` directive)
- Can use React hooks and browser APIs.
- Can handle user interactions.
- Still server-rendered on first load (SSR), then hydrated.
- Keep them as leaf nodes — push `"use client"` as far down as possible.

### Decision Rule
Ask: "Does this component need interactivity or browser APIs?"
- **No** → Server Component (default). Fetch data here.
- **Yes** → Client Component. Keep it small. Import it INTO a server component.

```tsx
// app/dashboard/page.tsx — Server Component (fetches data)
import { AnalysisCard } from "@/components/dashboard/AnalysisCard"; // client

export default async function Dashboard() {
  const analyses = await fetchAnalyses(); // server-side fetch
  return (
    <div>
      {analyses.map(a => <AnalysisCard key={a.id} {...a} />)}
    </div>
  );
}
```

</section>

<section id="data-fetching">

## Data Fetching

### In Server Components
Fetch directly — no `useEffect`, no loading state management:
```tsx
async function StockInfo({ symbol }: { symbol: string }) {
  const data = await fetch(`${API_URL}/api/analysis/${symbol}`);
  const analysis = await data.json();
  return <div>{analysis.summary}</div>;
}
```

### Caching & Revalidation
- `fetch()` in Server Components is automatically cached by default.
- Time-based revalidation: `fetch(url, { next: { revalidate: 60 } })` — ISR.
- On-demand revalidation: `revalidatePath('/dashboard')` or `revalidateTag('analysis')`.
- No cache: `fetch(url, { cache: 'no-store' })` — SSR every request.
- Route segment config: `export const dynamic = 'force-dynamic'` forces SSR.

### For MyApp
- Stock analysis results: cache with revalidation (data changes periodically).
- Persona sentiment: cache with shorter TTL (LLM-generated, may update).
- Dashboard: ISR with 60s revalidation.
- Auth pages: no cache (`force-dynamic`).

</section>

<section id="routing-patterns">

## Routing Patterns

### Dynamic Routes
`app/analysis/[id]/page.tsx` → `/analysis/abc123`
```tsx
export default async function AnalysisPage({
  params,
}: {
  params: { id: string };
}) {
  const analysis = await getAnalysis(params.id);
  return <AnalysisDetail analysis={analysis} />;
}
```

### Route Groups
`(marketing)` and `(app)` — different layouts, same URL space:
```
app/
├── (marketing)/      # Public pages — minimal layout
│   ├── layout.tsx
│   └── page.tsx      # Landing page at /
├── (app)/            # Authenticated pages — dashboard layout
│   ├── layout.tsx
│   └── dashboard/
│       └── page.tsx  # Dashboard at /dashboard
```

### Parallel Routes (Future)
`@modal` slots for modal overlays without losing page state.

</section>

<section id="server-actions">

## Server Actions

For mutations (create, update, delete) without API routes:
```tsx
// app/actions.ts
"use server";

export async function createAnalysis(formData: FormData) {
  const symbol = formData.get("symbol") as string;
  const response = await fetch(`${API_URL}/api/analysis/predict`, {
    method: "POST",
    body: JSON.stringify({ symbol }),
  });
  revalidatePath("/dashboard");
  return response.json();
}
```

</section>

<section id="middleware">

## Middleware
`middleware.ts` at project root. Runs before every request.
Use for: redirects, auth checks (NOT as sole auth — defense in depth),
geo-routing, A/B testing headers.

**Security warning:** Never rely solely on middleware for auth. Always verify
at the data access layer too.

</section>

<section id="streaming">

## Streaming & Loading States
`loading.tsx` creates automatic Suspense boundaries:
```
app/dashboard/
├── loading.tsx    # Shows while page.tsx loads
├── page.tsx       # Async server component
```

For granular streaming, wrap slow components in `<Suspense>`:
```tsx
<Suspense fallback={<AnalysisSkeleton />}>
  <SlowAnalysisComponent />
</Suspense>
```

</section>

<section id="api-proxy-pattern">

## API Proxy Pattern (MyApp)
Frontend proxies API calls to the FastAPI backend via `next.config.js` rewrites:
```js
async rewrites() {
  return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
}
```
This avoids CORS issues in development and simplifies deployment.

</section>

<section id="deployment">

## Deployment
- Docker: multi-stage build (`npm ci` → `npm run build` → `next start`).
- Standalone output: `output: 'standalone'` in `next.config.js` for minimal
  Docker images.
- Environment variables: `NEXT_PUBLIC_*` for client-side, regular for server-side.

</section>
