# React 19 & Frontend Reference

Colby reads this when working on React components or frontend-heavy features.

---

<section id="react-19">

## React 19 Fluency

### New APIs
- `use()` — read resources (promises, context) in render. Replaces many
  `useEffect` + `useState` fetch patterns.
- `useFormStatus` — access parent form's pending state from inside the form.
- `useActionState` — manage form action state (replaces `useFormState`).
- `useOptimistic` — optimistic UI updates that revert on server failure.
- `Actions API` — async functions in `action` / `formAction` props for
  mutations. Works with `startTransition`.
- `ref-as-prop` — ref is now a regular prop, no more `forwardRef` wrapper.
- `startTransition` — mark state updates as non-urgent for better responsiveness.
- `useDeferredValue` — defer expensive re-renders until idle.
- Suspense boundaries — wrap lazy-loaded or async components.

### React Compiler (React Forget)
- Automatically memoizes components, hooks, and values.
- Manual `useMemo`, `useCallback`, `React.memo` are rarely needed.
- Don't fight the compiler — write idiomatic code and let it optimize.
- Still useful to understand memoization for debugging performance issues.

### Component Patterns
- Functional components only. No class components.
- Props typed with TypeScript interfaces, not inline types.
- Discriminated unions for component variants:
  ```tsx
  type ButtonProps =
    | { variant: "primary"; loading?: boolean }
    | { variant: "ghost"; icon: ReactNode };
  ```
- Composition over configuration — prefer children/slots over prop explosion.
- Keep components under 150 lines. Extract hooks for logic, subcomponents for UI.

### Accessibility (Non-Negotiable)
- Semantic HTML first: `<button>`, `<nav>`, `<main>`, `<dialog>`, `<form>`.
- Every interactive element keyboard-accessible (Tab, Enter, Escape, Arrow keys).
- ARIA attributes when semantic HTML isn't sufficient.
- Color contrast AA minimum (4.5:1 text, 3:1 large text).
- Focus management: trap focus in modals, restore on close.
- Screen reader testing: use `aria-live` for dynamic content.

### State Management
- `useState` / `useReducer` for local state.
- Context for cross-cutting concerns (theme, auth, locale) — NOT for
  frequently-changing data (causes re-render storms).
- Server state belongs in the server (Next.js RSC) or a cache layer, not
  React state.

### Performance Patterns
- Lazy load routes and heavy components with `React.lazy` + Suspense.
- Virtualize long lists (react-window, tanstack-virtual).
- Debounce user input that triggers expensive operations.
- Avoid creating objects/arrays in render — hoist constants.
- Profile before optimizing. React DevTools Profiler, not guesswork.

</section>

---

<section id="tailwind-css-patterns">

## Tailwind CSS Patterns

### MyApp Design Tokens
- `brand-*` (50-950) — Primary indigo palette.
- `gain` / `gain-light` / `gain-dark` — Green for positive price movement.
- `loss` / `loss-light` / `loss-dark` — Red for negative price movement.
- `font-sans` — Inter. `font-mono` — JetBrains Mono.

### Conditional Classes
Always use `clsx` (already installed):
```tsx
import clsx from "clsx";
<span className={clsx(
  "rounded-full px-3 py-1 text-xs font-semibold",
  isBullish ? "bg-gain-light text-gain-dark" : "bg-loss-light text-loss-dark"
)} />
```

### Responsive
Mobile-first. Use `sm:`, `md:`, `lg:`, `xl:` breakpoints.
Dashboard grid: `grid gap-6 md:grid-cols-2 lg:grid-cols-3`.

### Dark Mode (Future)
When added, use `dark:` variant classes. Design tokens should support both
modes from the start.

</section>
