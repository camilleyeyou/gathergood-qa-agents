<!-- GSD:project-start source:PROJECT.md -->
## Project

**GatherGood**

GatherGood is an event management platform for community organizations — nonprofits, libraries, volunteer groups — to create events, sell or RSVP tickets, manage attendees, and check in guests with QR codes. It covers the full lifecycle from organization setup through post-event analytics.

**Core Value:** Community organizers can create an event, publish it, and have people register (free or paid) with working tickets and QR check-in — the end-to-end happy path must work flawlessly.

### Constraints

- **Tech stack**: Django REST Framework + Next.js + PostgreSQL + Stripe — per spec requirements
- **Deployment**: Vercel (frontend) + Railway (backend + DB) — target platforms
- **API contract**: Must match TEST_SPEC.md endpoint signatures, request/response shapes, and status codes exactly
- **Permission model**: Three-tier roles (OWNER > MANAGER > VOLUNTEER) with specific permission boundaries per the spec
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Django | 5.2.x (LTS) | Backend web framework | LTS release (April 2025 – April 2028). Prefer over 6.0.x because Railway deployments should target a stable, multi-year support window. 6.0.x mainstream support ends August 2026 — too short for a greenfield build. |
| Django REST Framework | 3.17.1 | REST API layer | Industry standard for Django APIs. Supports Django 5.2 + Python 3.10+. Browsable API speeds development. Robust permission system maps directly to the three-tier role model (OWNER > MANAGER > VOLUNTEER). |
| PostgreSQL | 16 | Primary database | Already decided. Native JSON support, full-text search, and LISTEN/NOTIFY all usable without extra infrastructure. Well-supported on Railway. |
| Next.js | 16.2.1 | Frontend framework | Current stable. Turbopack is now default for builds (stable), React Compiler is stable, App Router is the only recommended router. Deploy to Vercel with zero config. |
| React | 19.2 | UI runtime | Ships with Next.js 16. Server Components and Server Actions are first-class — use them for data fetching to avoid waterfall client requests. |
| TypeScript | 5.x (bundled) | Type safety | Included with Next.js 16. Zod schemas automatically generate TypeScript types — write validation once, use everywhere. |
### Backend Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| djangorestframework-simplejwt | 5.5.1 | JWT authentication | Required by spec: 30-min access tokens, 7-day refresh with rotation. Configure `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True`. |
| django-cors-headers | 4.9.0 | Cross-origin headers | Required for Next.js frontend on Vercel to call the Railway API. Set `CORS_ALLOWED_ORIGINS` explicitly — never use `CORS_ALLOW_ALL_ORIGINS = True` in production. |
| django-filter | 25.2 | QuerySet filtering | Powers search, category/format filters on public event browse. Integrates with DRF's `filter_backends`. |
| stripe | 15.0.0 | Stripe payment processing | Python SDK for server-side PaymentIntent creation, webhook verification, and refunds. Version 15 is a major release (March 2026) — review changelog before pinning. |
| qrcode | 8.2 | QR code generation | Generates QR images for ticket payloads. Use with `pillow` for PNG output. The HMAC-SHA256 signing is handled separately in Python `hmac` stdlib — do not use a third-party signing library. |
| Pillow | 12.1.1 | Image processing | Required by `qrcode` for PNG output. Also handles any event banner/image processing. |
| celery | 5.6.3 | Async task queue | Used for: email confirmation sending, reminder emails, bulk send, CSV export generation. Prevents blocking the request cycle on slow operations. |
| python-decouple | 3.8 | Environment variable management | Reads `.env` files and casts types correctly (`cast=bool`, `cast=int`). Simpler than `django-environ` for this use case — no URL parsing needed separately. |
| gunicorn | 25.3.0 | WSGI server | Standard production server for Django on Railway. Use `gunicorn app.wsgi:application --workers 2 --bind 0.0.0.0:$PORT`. |
| whitenoise | 6.12.0 | Static file serving | Serves Django admin static files directly from gunicorn without a separate CDN. Required for Railway deployments where a CDN is not in front of the backend. |
| psycopg2-binary | 2.9.11 | PostgreSQL adapter | Binary distribution — no build toolchain needed on Railway. Use `psycopg2-binary` in development and production (Railway's build environment handles this fine). |
| django-storages | 1.14.6 | Cloud file storage | Only needed if event images or CSV exports are stored in S3/GCS. Defer if files are served directly or not supported in v1. |
### Frontend Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @stripe/stripe-js | latest (^6.x) | Stripe.js loader | Loads Stripe.js asynchronously and exposes `stripe` instance. Required for PCI-compliant card collection. |
| @stripe/react-stripe-js | 6.0.0 | React Stripe Elements | `<Elements>`, `<PaymentElement>` components that render Stripe's hosted card form in an iframe. Keeps your Next.js app out of PCI scope. |
| @tanstack/react-query | 5.95.0 | Server state / async data | Handles all API data fetching, caching, background refetching, and optimistic updates. Use for: event lists, order status, check-in stats polling. The live check-in poll (`setInterval` + refetch) is built-in with `refetchInterval`. |
| zustand | 5.0.12 | Client UI state | Lightweight store for auth tokens (access + refresh), user profile, and cart state during checkout. Does not replace TanStack Query — used only for local UI state that does not come from the API. |
| react-hook-form | 7.72.0 | Form state management | Uncontrolled form inputs — minimal re-renders. Use for: registration, login, event creation, ticket tier forms. Integrates via `zodResolver`. |
| zod | 4.3.6 | Schema validation | TypeScript-first schema validation. Schemas are defined once and used for both client-side form validation and server action validation. `z.infer<>` generates TypeScript types automatically. |
| tailwindcss | 4.2.2 | CSS utility framework | v4 (current) uses CSS-native cascade layers and `@property` — no `tailwind.config.js` required. Zero-config setup with `@import "tailwindcss"` in your CSS. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| pytest-django | 4.12.0 | Django test runner | Use `@pytest.mark.django_db` decorator pattern. Faster than `unittest` for this project's test volume. |
| factory-boy | 3.3.3 | Test fixture factories | Generates model instances with realistic data. Define `OrganizationFactory`, `EventFactory`, `TicketTierFactory` etc. Avoids brittle fixture files. |
| coverage / pytest-cov | 7.13.5 | Test coverage | Run with `pytest --cov=. --cov-report=term-missing`. Aim for >90% on core checkout and QR flows. |
| black | latest | Python code formatting | Zero-config formatter. Run in pre-commit. |
| ruff | latest | Python linter | Replaces flake8 + isort. Fast, single tool. |
| eslint | bundled with Next.js | JS/TS linting | Next.js 16 includes `eslint-config-next`. Run `next lint` in CI. |
## Installation
### Backend (Python / Django)
# Core
# Dev
### Frontend (Node / Next.js)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Django 5.2 LTS | Django 6.0.x | If you need the very latest Django features (composite PKs, etc.) and can accept shorter support window (ends Aug 2026) |
| python-decouple | django-environ | django-environ is better when you need `env.db()` URL parsing or `env.cache()` — not needed here since Railway injects `DATABASE_URL` directly |
| @tanstack/react-query | SWR | SWR is simpler but lacks mutation handling, optimistic updates, and `refetchInterval` — all needed for check-in polling and order management |
| zustand | Redux Toolkit | Redux is justified for very large apps with complex cross-feature state. Overkill here — auth + cart is all this project needs from a client store. |
| celery + Redis | Django Q2, Dramatiq | Celery has the deepest Railway template support and the best documentation. Stick with it unless you have a specific reason to deviate. |
| react-hook-form | Formik | Formik is older, uses controlled inputs (more re-renders), and has slower TypeScript support. react-hook-form is the current community standard. |
| tailwindcss v4 | tailwindcss v3 | v3 still works if you need broad third-party component library support (Shadcn, DaisyUI). v4 is recommended for new projects but some Shadcn components may need updates. |
| @stripe/react-stripe-js PaymentElement | Custom card form | Never build a custom card form. Stripe's PaymentElement keeps you out of PCI scope and handles 3D Secure automatically. |
| psycopg2-binary | psycopg3 (psycopg) | psycopg3 is the newer async-capable adapter. Use it if you add Django Channels later. For sync Django + gunicorn, psycopg2-binary is simpler. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `djangorestframework-jwt` (PyJWT wrapper) | Unmaintained, superseded | `djangorestframework-simplejwt` |
| `dj-rest-auth` | Adds significant complexity with limited benefit for this spec's auth model | Implement JWT endpoints directly with simplejwt as the spec defines them |
| `django-allauth` | OAuth/social login is explicitly out of scope for v1 | Roll simple email+password auth per spec |
| Next.js Pages Router | Deprecated direction, lacks Server Components and React 19 features | App Router (already the default in Next.js 16) |
| `axios` for Next.js server components | Does not integrate with Next.js native `fetch` caching/revalidation | Use native `fetch` in Server Components; use TanStack Query in Client Components |
| `moment.js` | 66KB, unmaintained | `date-fns` (tree-shakeable) or native `Intl.DateTimeFormat` for timezone display |
| `django-celery` (old package) | Deprecated, merged into Celery core in v4 | `celery` directly — `from celery import Celery` |
| `Stripe.js` loaded via `<script>` tag | Bypasses loading optimisation and type safety | `@stripe/stripe-js` `loadStripe()` which lazy-loads and memoizes the instance |
| SQLite for any environment | No JSON operators, no concurrent writes, behavior differs from PostgreSQL 16 | Always use PostgreSQL (even in local dev via Docker or Railway dev environment) |
## Stack Patterns by Variant
- Skip the Stripe PaymentIntent creation entirely on the backend
- POST to `/checkout/` returns order directly with `payment_status: "free"`
- No `@stripe/react-stripe-js` components rendered in the UI for free tiers
- Backend creates `PaymentIntent`, returns `client_secret`
- Frontend renders `<Elements>` + `<PaymentElement>` with the `client_secret`
- On `stripe.confirmPayment()` success, frontend polls or receives redirect with `payment_intent` in URL
- Backend confirms via Stripe webhook (`payment_intent.succeeded`) — do not trust frontend-only confirmation
- Use the browser's `navigator.mediaDevices.getUserMedia` + a QR scanning library (e.g., `html5-qrcode` or `zxing-js/browser`) — no React Native needed
- Polling for check-in stats uses TanStack Query `refetchInterval: 5000`
- Use `celery` + Redis for async email sending
- Configure `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'` in production
- For Railway: add a Redis service, set `CELERY_BROKER_URL = env('REDIS_URL')`
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Django 5.2.x | djangorestframework 3.17.x | DRF 3.16 added Django 5.1/5.2 support; 3.17.x is current |
| Django 5.2.x | djangorestframework-simplejwt 5.5.1 | simplejwt 5.x supports Django 4.2 through 5.2 |
| Django 5.2.x | django-cors-headers 4.9.0 | Requires Python >=3.9, compatible |
| Django 5.2.x | celery 5.6.3 | Celery 5.x supports Django 4.2+ |
| stripe 15.0.0 | @stripe/react-stripe-js 6.0.0 | Both released March 2026; major version bumps — verify API changes in Stripe changelog before pinning |
| Next.js 16.2.1 | React 19.2 | Next.js 16 requires React 19.x |
| zod 4.x | @hookform/resolvers | Requires `@hookform/resolvers` >=3.x which supports Zod 4 |
| tailwindcss 4.x | Next.js 16 | Next.js `create-next-app --tailwind` installs v4 by default now |
| psycopg2-binary 2.9.11 | PostgreSQL 16 | psycopg2 2.9.x supports PG 16 fully |
## Sources
- [PyPI djangorestframework](https://pypi.org/project/djangorestframework/) — version 3.17.1 verified
- [PyPI djangorestframework-simplejwt](https://pypi.org/project/djangorestframework-simplejwt/) — version 5.5.1 verified
- [PyPI django-cors-headers](https://pypi.org/project/django-cors-headers/) — version 4.9.0 verified
- [PyPI stripe](https://pypi.org/project/stripe/) — version 15.0.0 verified
- [PyPI celery](https://pypi.org/project/celery/) — version 5.6.3 verified
- [PyPI django-filter](https://pypi.org/project/django-filter/) — version 25.2 verified
- [PyPI qrcode](https://pypi.org/project/qrcode/) — version 8.2 verified
- [PyPI Pillow](https://pypi.org/project/Pillow/) — version 12.1.1 verified
- [PyPI gunicorn](https://pypi.org/project/gunicorn/) — version 25.3.0 verified
- [PyPI whitenoise](https://pypi.org/project/whitenoise/) — version 6.12.0 verified
- [PyPI psycopg2-binary](https://pypi.org/project/psycopg2-binary/) — version 2.9.11 verified
- [PyPI python-decouple](https://pypi.org/project/python-decouple/) — version 3.8 verified
- [PyPI pytest-django](https://pypi.org/project/pytest-django/) — version 4.12.0 verified
- [PyPI factory-boy](https://pypi.org/project/factory-boy/) — version 3.3.3 verified
- [Django download page](https://www.djangoproject.com/download/) — 5.2 LTS vs 6.0.x guidance verified
- [Next.js 16.2 announcement](https://medium.com/@onix_react/release-next-js-16-2-377798369d25) — 16.2.1 current version, MEDIUM confidence (not official Next.js blog post)
- [Next.js 16 blog](https://nextjs.org/blog/next-16) — React Compiler stable, Turbopack default, React 19.2 confirmed
- [npm @stripe/react-stripe-js](https://www.npmjs.com/package/@stripe/react-stripe-js) — version 6.0.0 confirmed
- [npm zustand](https://www.npmjs.com/package/zustand) — version 5.0.12 confirmed
- [npm @tanstack/react-query](https://www.npmjs.com/package/@tanstack/react-query) — version 5.95.0 confirmed
- [npm react-hook-form](https://www.npmjs.com/package/react-hook-form) — version 7.72.0 confirmed
- [npm zod](https://www.npmjs.com/package/zod) — version 4.3.6 confirmed
- [tailwindcss v4 blog](https://tailwindcss.com/blog/tailwindcss-v4) — v4.2.2 current, zero-config install
- [Railway Django + Celery + Redis template](https://railway.com/deploy/NBR_V3) — deployment architecture pattern
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
