# CSS and Tailwind best practices

Read by: teams working on starter-web projects. Extends nextjs.md.

## Read before you write

Before creating or modifying ANY UI element:

1. Read `src/components/ui/` — know what primitives exist (Button, Card, Input, etc.)
2. Read `tailwind.config.ts` — know the colour tokens, spacing scale, fonts, and breakpoints
3. Read the component you are changing — match its existing patterns

If a component already exists, use it. If a design token already exists, use it.

```tsx
// WRONG — guessing that a wrapper class exists
<div className="card-wrapper">
  <div className="card-header">...</div>
</div>

// RIGHT — read src/components/ui/ first, use the actual component
import { Card, CardHeader } from "@/components/ui/card";
<Card>
  <CardHeader>...</CardHeader>
</Card>
```

## Utility-first Tailwind

- All styling via Tailwind utility classes — no CSS modules, no styled-components
- `@apply` only in `globals.css` for base-level resets or Tailwind directive layers
- Compose utilities inline rather than creating custom CSS classes

```css
/* globals.css — acceptable @apply usage */
@layer base {
  body {
    @apply bg-background text-foreground;
  }
}
```

```tsx
// WRONG — custom CSS class
<button className="btn btn-primary">Save</button>

// RIGHT — utility composition (or better: use the Button component)
<button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
  Save
</button>
```

## Colour system

Use semantic tokens from `tailwind.config.ts`. Never hardcode hex values or use generic Tailwind palette colours when a design system is configured.

```tsx
// WRONG — hardcoded hex
<div className="bg-[#1a1a2e] text-[#e0e0e0]">

// WRONG — generic Tailwind palette when design tokens exist
<div className="bg-blue-500 text-gray-100">

// RIGHT — semantic tokens from the project config
<div className="bg-primary text-primary-foreground">
<div className="bg-surface text-foreground">
<div className="border border-muted">
```

Read `tailwind.config.ts` to discover the actual token names — they vary per project.

## Responsive design

Mobile-first: bare utilities are the mobile style, breakpoint prefixes add larger-screen overrides.

Standard breakpoints: `sm` (640px), `md` (768px), `lg` (1024px), `xl` (1280px).

```tsx
// Mobile: single column, stacked. Tablet+: two columns. Desktop: three columns.
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
  ...
</div>

// Mobile: full width. Desktop: constrained and centered.
<main className="px-4 md:px-6 lg:mx-auto lg:max-w-5xl">
  ...
</main>
```

## Component patterns

Extract repeated class combinations into React components, not utility classes or `@apply` blocks.

```tsx
// WRONG — a .btn utility class in CSS
// WRONG — copy-pasting the same 8 classes across 12 files

// RIGHT — a component in src/components/ui/button.tsx
export function Button({ children, variant = "default", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors",
        variants[variant],
        sizes[size],
      )}
      data-testid={props["data-testid"]}
      {...props}
    >
      {children}
    </button>
  );
}
```

Component locations:
- `src/components/ui/` — generic primitives (Button, Card, Input, Dialog, Badge)
- `src/components/{feature}/` — feature-specific compositions (ThreadList, EventCard)

## Typography

Use the project's font and type scale from `tailwind.config.ts`. Standard scale tokens: `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, `text-3xl`.

```tsx
// WRONG — arbitrary pixel value when a scale token exists
<p className="text-[14px] leading-[1.4]">

// RIGHT — scale token
<p className="text-sm leading-normal">
```

## Spacing

Use the Tailwind spacing scale consistently. Within a single component, use the same spacing value for similar structural roles.

```tsx
// WRONG — inconsistent spacing for the same role
<div className="p-3">
  <h2 className="mb-4">Title</h2>
  <p className="mb-3">Body</p>  {/* why 3 here and 4 above? */}
</div>

// RIGHT — consistent spacing
<div className="p-4">
  <h2 className="mb-2">Title</h2>
  <p className="mb-2">Body</p>
</div>
```

## Layout

Common layout patterns with flex and grid:

```tsx
// Stacked vertical layout with consistent gap
<div className="flex flex-col gap-4">
  <Header />
  <Content />
  <Footer />
</div>

// Responsive grid
<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
  {items.map(item => <Card key={item.id} />)}
</div>

// Centered content container
<div className="mx-auto max-w-4xl px-4">
  ...
</div>

// Horizontal bar with items pushed apart
<div className="flex items-center justify-between">
  <Logo />
  <Nav />
</div>
```

## Dark mode

If the project uses dark mode, every custom colour must have a `dark:` counterpart. Semantic tokens in `tailwind.config.ts` should handle this automatically via CSS variables — verify before adding manual `dark:` overrides.

```tsx
// If using CSS variable-based tokens (most projects), this just works:
<div className="bg-background text-foreground">

// If adding a one-off colour, always include dark variant:
<div className="bg-white dark:bg-gray-900">
```

## Animations and transitions

Use Tailwind transition utilities for hover and focus states. Keep animations subtle.

```tsx
// Hover colour transition
<button className="bg-primary transition-colors duration-150 hover:bg-primary/90">

// Focus ring
<input className="rounded-md border border-input ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
```

## Prettier plugin

`prettier-plugin-tailwindcss` is installed and auto-sorts class names on format. Do not manually reorder classes — run `npm run format` and let the plugin handle ordering.

## data-testid attributes

Every interactive UI element must have a `data-testid` for browser testing. Convention: `{component}-{element}`.

```tsx
<button data-testid="sidebar-nav-link" className="...">Dashboard</button>
<input data-testid="login-email-input" className="..." />
<form data-testid="settings-form" className="...">
<a data-testid="header-logo-link" href="/">...</a>
```

Non-interactive display elements do not need `data-testid` unless they are asserted on in tests.

NEVER:
- Guess class names or component APIs — read the source first
- Hardcode hex colours or use generic palette colours when semantic tokens exist
- Use CSS modules, styled-components, or Sass
- Create `.btn`, `.card`, or `.input` utility classes — make React components instead
- Use arbitrary values (`[14px]`, `[#ff0000]`) when a Tailwind scale token or design token covers the value
- Manually reorder Tailwind classes — let prettier-plugin-tailwindcss handle it
- Skip `data-testid` on interactive elements
- Add `@apply` outside of `globals.css` base layer
