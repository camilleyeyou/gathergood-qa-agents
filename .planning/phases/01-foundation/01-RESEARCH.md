# Phase 1: Foundation - Research

**Researched:** 2026-03-28
**Domain:** Django JWT authentication, organization RBAC, venue management, Next.js App Router with shadcn/ui
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User can register with email, password, first name, and last name | djangorestframework-simplejwt custom RegisterView + custom User model; Zod + react-hook-form on frontend |
| AUTH-02 | User can log in with email/password and receive JWT access + refresh tokens | simplejwt TokenObtainPairView; 30min/7-day config; access in memory, refresh in HttpOnly cookie |
| AUTH-03 | User can refresh an expired access token using a valid refresh token (rotation enabled) | simplejwt TokenRefreshView with ROTATE_REFRESH_TOKENS=True + BLACKLIST_AFTER_ROTATION=True |
| AUTH-04 | User can request a password reset email | Custom view using Django's PasswordResetForm or manual uid/token generation; email sent via Django email backend |
| AUTH-05 | User can reset password via emailed uid + token link | Django's PasswordResetConfirmView pattern; custom DRF endpoint accepting uid + token + new password |
| PROF-01 | User can view their own profile (GET /auth/me/) | Authenticated DRF view returning serialized User; TanStack Query on frontend |
| PROF-02 | User can update their first name, last name, phone, and avatar URL | PATCH endpoint with partial serializer; react-hook-form + Zod on frontend |
| ORG-01 | Authenticated user can create an organization (auto-assigned OWNER role) | Organization model + OrganizationMember join model; signal or service auto-creates OWNER membership |
| ORG-02 | User can list organizations where they are a member | Queryset filtered by OrganizationMember; TanStack Query on frontend with loading/empty/populated states |
| ORG-03 | OWNER or MANAGER can update organization details | DRF custom permission class checking OrganizationMember role; PATCH/PUT endpoint |
| ORG-04 | Organization slug is auto-generated from name with dedup suffix | slugify() + suffix loop in services.py; common/utils.py generate_unique_slug() helper |
| TEAM-01 | OWNER or MANAGER can invite a member by email with a role assignment | Invite endpoint creates OrganizationMember (or Invitation model); permission check in view |
| TEAM-02 | MANAGER cannot assign the OWNER role when inviting | Serializer-level validation + permission class; also enforced client-side with Select options |
| TEAM-03 | Any org member can list team members | Queryset gated by any OrganizationMember role check; Table + Skeleton on frontend |
| TEAM-04 | Only OWNER can remove a member from the organization | DRF permission class IsOrganizationOwner; confirm Dialog on frontend |
| VENU-01 | Org member can create a venue with all required fields | Venue model scoped to Organization; serializer validates required fields; Dialog form on frontend |
| VENU-02 | Org member can list venues for their organization | Queryset filtered by org; Table with Skeleton loading on frontend |
| VENU-03 | Org member can update a venue | PATCH endpoint on Venue; same Dialog form (edit mode) reused for create |
</phase_requirements>

---

## Summary

Phase 1 is the greenfield foundation of the GatherGood platform. It establishes the backend Django project structure, all authentication flows (register, login, token refresh, password reset), user profile management, organization CRUD with three-tier RBAC (OWNER > MANAGER > VOLUNTEER), team member invitation and removal, and venue management. The frontend scaffold initializes Next.js 16 with App Router, shadcn/ui on Tailwind v4, and establishes the auth-aware navbar and all Phase 1 screens per the approved UI-SPEC.

The most important architectural decisions that must be made correctly in Phase 1 and cannot easily be retrofitted are: secure JWT token storage (access in memory, refresh in HttpOnly cookie), object-level DRF permission checks for org membership, slug uniqueness strategy using database-level deduplication, and the service-layer pattern (thin views, business logic in services.py). Every subsequent phase inherits these patterns.

The UI-SPEC has been approved and defines exact interaction contracts, component selections (all from the official shadcn registry), copy strings, color tokens, and accessibility requirements. The planner must treat the UI-SPEC as a locked constraint — no design decisions remain open for Phase 1 frontend work.

**Primary recommendation:** Build backend (Django project scaffold + accounts app + organizations app) in Wave 1, then frontend (Next.js scaffold + auth screens + manage screens) in Wave 2. Both waves can share a Wave 0 that sets up environments and test infrastructure.

---

## Standard Stack

### Core (Phase 1 active)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2.x LTS | Backend framework | LTS through April 2028; stable for Railway deployment |
| djangorestframework | 3.17.1 | REST API layer | Industry standard; permission system maps to OWNER/MANAGER/VOLUNTEER model |
| djangorestframework-simplejwt | 5.5.1 | JWT auth | Spec requires 30min access + 7-day refresh with rotation; BLACKLIST app required |
| django-cors-headers | 4.9.0 | CORS | Railway backend + Vercel frontend require explicit CORS config |
| psycopg2-binary | 2.9.11 | PostgreSQL adapter | Binary; no build toolchain needed on Railway |
| python-decouple | 3.8 | Env var management | Reads .env, casts types; simpler than django-environ for this use case |
| gunicorn | 25.3.0 | WSGI server | Standard for Django on Railway |
| whitenoise | 6.12.0 | Static file serving | Required for Django admin statics on Railway (no CDN in front of backend) |
| Next.js | 16.2.1 | Frontend framework | Current stable; App Router only; Vercel zero-config deploy |
| React | 19.2 | UI runtime | Ships with Next.js 16 |
| TypeScript | 5.x | Type safety | Bundled with Next.js 16 |
| tailwindcss | 4.2.2 | CSS utility framework | v4 zero-config; CSS-native; `@import "tailwindcss"` only — no tailwind.config.js |
| shadcn/ui | (CLI-based) | Component library | Approved in UI-SPEC; official registry only; already initialized per UI-SPEC frontmatter |
| react-hook-form | 7.72.0 | Form state | Uncontrolled inputs; integrates with zodResolver |
| zod | 4.3.6 | Schema validation | TypeScript-first; `z.infer<>` generates types; used for both client validation and API types |
| @tanstack/react-query | 5.95.0 | Server state | Handles fetch, caching, loading states; `refetchInterval` for later polling needs |
| zustand | 5.0.12 | Client UI state | Auth tokens + user profile store; memory storage for access token |
| lucide-react | (bundled via shadcn) | Icons | Specified in UI-SPEC; Eye icon for password show/hide, Menu icon for hamburger |

### Supporting (Phase 1 needed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @hookform/resolvers | >=3.x | Zod/RHF bridge | Required for zodResolver() integration |
| pytest-django | 4.12.0 | Django test runner | All Django unit/integration tests use @pytest.mark.django_db |
| factory-boy | 3.3.3 | Test fixtures | UserFactory, OrganizationFactory, OrganizationMemberFactory — avoids brittle fixtures |
| pytest-cov | (pinned with coverage 7.13.5) | Coverage | Run with --cov=. --cov-report=term-missing |
| black | latest | Python formatting | Zero-config; run in pre-commit |
| ruff | latest | Python linting | Replaces flake8 + isort; fast |

### Not Needed in Phase 1

| Deferred Library | Reason |
|------------------|--------|
| stripe / @stripe/stripe-js | Phase 3 (checkout) |
| qrcode / Pillow | Phase 4 (QR check-in) |
| celery | Phase 5 (email async); defer until email confirmed in scope |
| django-filter | Phase 2 (public event browse search) |
| django-storages | Only if image upload added; not in v1 scope |

### Installation

**Backend:**
```bash
pip install Django==5.2.12
pip install djangorestframework==3.17.1
pip install djangorestframework-simplejwt==5.5.1
pip install django-cors-headers==4.9.0
pip install psycopg2-binary==2.9.11
pip install python-decouple==3.8
pip install gunicorn==25.3.0
pip install whitenoise==6.12.0

# Dev / test
pip install pytest-django==4.12.0
pip install factory-boy==3.3.3
pip install coverage==7.13.5
pip install pytest-cov
pip install black
pip install ruff
```

**Frontend (from project root, frontend/ directory):**
```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*"

npm install @tanstack/react-query
npm install zustand
npm install react-hook-form zod @hookform/resolvers
npm install lucide-react

# shadcn init (Tailwind v4 CSS-native mode — no config file)
npx shadcn init

# Phase 1 components (from UI-SPEC Component Inventory)
npx shadcn add button input label form card dialog table badge avatar separator sonner dropdown-menu alert skeleton sheet
```

---

## Architecture Patterns

### Recommended Project Structure

**Backend:**
```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py          # shared: INSTALLED_APPS, AUTH, JWT config, simplejwt settings
│   │   ├── local.py         # dev: DEBUG=True, .env loading, test DB
│   │   └── production.py    # Railway: ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, whitenoise
│   ├── urls.py              # mounts /api/v1/ — include per-app urls
│   └── wsgi.py
├── apps/
│   ├── accounts/            # AUTH-01 through AUTH-05, PROF-01, PROF-02
│   │   ├── models.py        # CustomUser extending AbstractBaseUser or AbstractUser
│   │   ├── serializers.py   # RegisterSerializer, LoginSerializer, ProfileSerializer
│   │   ├── views.py         # thin HTTP adapters — delegate to services
│   │   ├── services.py      # create_user(), send_password_reset_email(), verify_reset_token()
│   │   ├── urls.py
│   │   └── tests/
│   │       ├── test_auth.py
│   │       └── factories.py # UserFactory
│   └── organizations/       # ORG-01 through ORG-04, TEAM-01 through TEAM-04, VENU-01 through VENU-03
│       ├── models.py        # Organization, OrganizationMember, Venue
│       ├── serializers.py   # OrgSerializer, MemberSerializer, VenueSerializer
│       ├── views.py
│       ├── services.py      # create_org(), invite_member(), remove_member(), generate_slug()
│       ├── permissions.py   # IsOrgOwner, IsOrgManager, IsOrgOwnerOrManager, IsOrgMember
│       ├── urls.py
│       └── tests/
│           ├── test_organizations.py
│           ├── test_team.py
│           ├── test_venues.py
│           └── factories.py # OrganizationFactory, OrganizationMemberFactory, VenueFactory
├── common/
│   ├── permissions.py       # base role-checking utilities imported by app permissions
│   ├── pagination.py
│   └── utils.py             # generate_unique_slug(name, model_class, slug_field='slug')
└── requirements/
    ├── base.txt
    └── production.txt
```

**Frontend:**
```
frontend/src/
├── app/
│   ├── layout.tsx            # root layout — QueryClientProvider, auth-aware navbar
│   ├── (auth)/               # route group — /register, /login, /forgot-password, /reset-password
│   │   ├── register/page.tsx
│   │   ├── login/page.tsx
│   │   ├── forgot-password/page.tsx
│   │   └── reset-password/page.tsx
│   ├── my/
│   │   └── settings/page.tsx # PROF-01, PROF-02 — /my/settings
│   └── manage/               # authenticated organizer dashboard
│       ├── layout.tsx        # dashboard shell with auth-aware navbar
│       ├── page.tsx          # org list — ORG-01, ORG-02
│       ├── org/
│       │   ├── new/page.tsx  # create org — ORG-01, ORG-04
│       │   └── [slug]/
│       │       ├── page.tsx          # org details — ORG-03
│       │       ├── team/page.tsx     # TEAM-01 through TEAM-04
│       │       └── venues/page.tsx   # VENU-01 through VENU-03
├── components/
│   ├── ui/                   # shadcn generated components (do not edit)
│   ├── layout/
│   │   └── Navbar.tsx        # auth-aware navbar per UI-SPEC
│   ├── auth/                 # RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
│   └── manage/               # OrgCard, OrgForm, TeamTable, InviteDialog, RemoveDialog, VenueTable, VenueDialog
├── lib/
│   ├── api/
│   │   ├── auth.ts           # register(), login(), refreshToken(), getMe(), updateProfile()
│   │   └── organizations.ts  # listOrgs(), createOrg(), updateOrg(), listMembers(), inviteMember(), removeMember(), listVenues(), createVenue(), updateVenue()
│   ├── auth.ts               # token storage: access in memory (module var), refresh via cookie
│   └── utils.ts              # cn() classname helper (from shadcn)
├── hooks/
│   └── useAuth.ts            # current user, logout, token refresh interceptor
└── types/
    ├── auth.ts               # User, LoginResponse, RegisterPayload types
    └── organizations.ts      # Organization, OrganizationMember, Venue types
```

### Pattern 1: JWT Secure Token Storage

**What:** Access tokens stored in module-level memory (not localStorage). Refresh tokens stored in HttpOnly, Secure, SameSite=Strict cookies. Backend sets the refresh token cookie on login and refresh; frontend never reads it directly.

**Why mandatory:** localStorage is readable by any JavaScript (XSS risk). The 30-minute access token lifetime limits exposure if the in-memory variable is somehow leaked. This pattern is non-negotiable per the project's security baseline (STATE.md).

**Frontend implementation:**
```typescript
// lib/auth.ts — module-level variable, not localStorage
let accessToken: string | null = null;

export const setAccessToken = (token: string) => { accessToken = token; };
export const getAccessToken = () => accessToken;
export const clearAccessToken = () => { accessToken = null; };
```

**Backend — set refresh token as HttpOnly cookie on login:**
```python
# accounts/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings

class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            refresh = response.data.pop('refresh')
            response.set_cookie(
                key='refresh_token',
                value=refresh,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Strict',
                max_age=7 * 24 * 60 * 60,  # 7 days
            )
        return response
```

### Pattern 2: DRF Object-Level Permission Checks

**What:** Each app has its own permissions.py that imports base role-checking utilities from common/permissions.py. Object-level permissions verify org membership by querying OrganizationMember for the requesting user and the org extracted from the URL kwargs.

**Critical nuance:** DRF's `has_object_permission()` is NOT called automatically — it only fires when the view explicitly calls `self.get_object()` (which triggers it) or explicitly calls `self.check_object_permissions(request, obj)`. Never call `queryset.filter(pk=pk).first()` and skip `get_object()`.

```python
# apps/organizations/permissions.py
from common.permissions import get_member_role

class IsOrgOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj is the Organization instance
        role = get_member_role(request.user, obj)
        return role in ('OWNER', 'MANAGER')

class IsOrgMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_member_role(request.user, obj)
        return role is not None  # any role

# common/permissions.py
def get_member_role(user, organization):
    """Returns role string or None if user is not a member."""
    try:
        return OrganizationMember.objects.get(
            user=user, organization=organization
        ).role
    except OrganizationMember.DoesNotExist:
        return None
```

### Pattern 3: Slug Auto-Generation with Dedup

**What:** Organization slugs are auto-generated from name using `django.utils.text.slugify()`. If the generated slug already exists, append a numeric suffix (-2, -3, ...) until unique.

**When to use:** ORG-04 requires this on org create. Same pattern reused for event slugs in Phase 2 (EVNT-03).

```python
# common/utils.py
from django.utils.text import slugify

def generate_unique_slug(name: str, model_class, slug_field: str = 'slug') -> str:
    base_slug = slugify(name)
    slug = base_slug
    n = 1
    while model_class.objects.filter(**{slug_field: slug}).exists():
        n += 1
        slug = f"{base_slug}-{n}"
    return slug
```

### Pattern 4: Service Layer — Thin Views

**What:** DRF views handle HTTP concerns only (auth, parsing, response serialization). Business logic — slug generation, auto-assigning OWNER role, MANAGER role restriction on invite — lives in services.py.

**Why:** Enables testing services in isolation; prevents fat-view anti-pattern; enables management commands that reuse service logic.

```python
# apps/organizations/services.py
from common.utils import generate_unique_slug
from .models import Organization, OrganizationMember

def create_organization(user, name: str) -> Organization:
    slug = generate_unique_slug(name, Organization)
    org = Organization.objects.create(name=name, slug=slug)
    OrganizationMember.objects.create(
        user=user, organization=org, role='OWNER'
    )
    return org

def invite_member(inviting_user, org, email: str, role: str) -> OrganizationMember:
    """Role must be MANAGER or VOLUNTEER. OWNER assignment blocked here."""
    if role == 'OWNER':
        raise PermissionError("Cannot assign OWNER role via invite.")
    # Get or create user by email, then create membership
    ...
```

### Pattern 5: simplejwt Configuration (Security-Correct)

**What:** Both `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` must be True together. Without the blacklist, old refresh tokens remain valid after rotation — enabling token replay attacks. The `rest_framework_simplejwt.token_blacklist` app must be in INSTALLED_APPS and migrated.

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # REQUIRED for rotation
    ...
]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Pattern 6: shadcn/ui on Tailwind v4

**What:** Tailwind v4 is CSS-native — no tailwind.config.js. shadcn tokens are declared as CSS variables in `:root` under `@layer base`. Import via `@import "tailwindcss"` in globals.css. The UI-SPEC defines exact CSS variable values.

**Note from STATE.md Blockers:** Tailwind v4 + shadcn/ui component compatibility should be verified. The UI-SPEC frontmatter confirms `shadcn_initialized: true` and `preset: none`, confirming the CSS-native path was tested and approved by the UI researcher.

```css
/* app/globals.css */
@import "tailwindcss";

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222 47% 11%;
    --muted: 220 14% 96%;
    --muted-foreground: 215 16% 47%;
    --primary: 173 80% 31%;     /* #0D9488 — teal accent */
    --primary-foreground: 0 0% 100%;
    --destructive: 0 72% 47%;   /* #DC2626 */
    --destructive-foreground: 0 0% 100%;
    --border: 220 13% 91%;
    --ring: 173 80% 31%;
  }
}
```

### Anti-Patterns to Avoid

- **Storing JWT in localStorage:** Never. Access token in module memory; refresh token in HttpOnly cookie. See Pitfall 7 (PITFALLS.md).
- **Calling queryset.filter(pk=pk).first() instead of get_object():** DRF object-level permissions only fire when get_object() is used. Bypassing it silently skips org membership checks.
- **MANAGER inviting OWNER — enforced only client-side:** Must also be validated in the serializer/service (TEAM-02). Frontend Select hiding OWNER option is UX; backend rejection is security.
- **ROTATE_REFRESH_TOKENS without BLACKLIST_AFTER_ROTATION:** Old refresh tokens remain valid. Must set both.
- **Business logic in views:** All slug generation, OWNER auto-assignment, member role validation must live in services.py.
- **Using dj-rest-auth or django-allauth for auth:** These add complexity; simplejwt endpoints directly per spec.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT access + refresh tokens | Custom token generation/signing | djangorestframework-simplejwt | Handles token creation, validation, blacklisting, rotation — all security-critical operations |
| Form validation + TypeScript types | Custom validator + interface | Zod schema + `z.infer<>` | One source of truth; eliminates type drift between validation and TypeScript interfaces |
| Form state management | Controlled inputs with useState | react-hook-form | Uncontrolled inputs; far fewer re-renders; built-in error state management |
| UI components (Button, Input, Dialog) | Custom HTML+CSS | shadcn/ui from official registry | Radix UI primitives with correct accessibility; already approved in UI-SPEC |
| Password reset token generation | Custom token system | Django's PasswordResetTokenGenerator | Cryptographically secure; handles expiry; widely tested |
| Loading / empty / error states | Custom state machines | TanStack Query (isLoading, isError, data) | Handles all async state transitions with proper caching |
| Slug uniqueness | Ad hoc string checks | generate_unique_slug() utility in common/utils.py | Race-condition-safe if combined with unique DB constraint; reusable in Phase 2 for events |

**Key insight:** The auth, validation, and UI component problems all have well-tested library solutions. Any custom implementation risks missing security edge cases (token replay, XSS, accessibility failures) that the libraries already handle correctly.

---

## Common Pitfalls

### Pitfall 1: DRF Object-Level Permissions Not Auto-Called

**What goes wrong:** A MANAGER from Organization B can read or edit Organization A's team or venues because `has_object_permission()` was never invoked — only `has_permission()` (view-level) fired.

**Why it happens:** DRF calls `has_permission()` automatically on every request, but `has_object_permission()` only fires when the view calls `self.get_object()`. Developers who retrieve objects via `queryset.filter(pk=pk).first()` silently bypass object checks.

**How to avoid:** Always use `self.get_object()` in DRF views. Write explicit cross-org access tests: create two orgs, log in as a MANAGER of Org B, attempt to hit Org A's endpoints, assert 403.

**Warning signs:** Permission classes only implement `has_permission()`. Integration tests only verify authorized access, not denied cross-org access.

### Pitfall 2: ROTATE_REFRESH_TOKENS Without BLACKLIST_AFTER_ROTATION

**What goes wrong:** After a token refresh, the old refresh token remains valid. An attacker who captured the old token can continue using it indefinitely.

**Why it happens:** Developers enable `ROTATE_REFRESH_TOKENS = True` but forget to add `rest_framework_simplejwt.token_blacklist` to INSTALLED_APPS and run migrations, so `BLACKLIST_AFTER_ROTATION = True` silently fails to blacklist anything.

**How to avoid:** Add `rest_framework_simplejwt.token_blacklist` to INSTALLED_APPS, run `manage.py migrate`, and verify that a used refresh token is rejected on the second use.

**Warning signs:** No `OutstandingToken` or `BlacklistedToken` tables in the database after migration.

### Pitfall 3: JWT Stored in localStorage (XSS Vulnerability)

**What goes wrong:** Any XSS injection in user-controlled content (e.g., a future event description) can exfiltrate the JWT from localStorage.

**Why it happens:** localStorage survives page reloads without extra setup, making it the path of least resistance.

**How to avoid:** Store access token in a module-level variable (cleared on page refresh — acceptable given 30-minute lifetime). Store refresh token in an HttpOnly, Secure, SameSite=Strict cookie set by the backend. Never call `localStorage.setItem('access_token', ...)`.

**Warning signs:** `localStorage.setItem` anywhere in frontend code. No cookie with `HttpOnly` flag in browser dev tools after login.

### Pitfall 4: MANAGER Can Assign OWNER Role (TEAM-02 Violation)

**What goes wrong:** A MANAGER sends a direct API POST to the invite endpoint with `role: "OWNER"`, bypassing the frontend Select that hides the OWNER option.

**Why it happens:** Only the frontend enforces the restriction. The backend serializer or service has no check.

**How to avoid:** Validate in the serializer: if `request.user`'s org role is MANAGER, reject any invite with `role == 'OWNER'`. Also validate in the service. Test by sending a raw API request as a MANAGER with role=OWNER and asserting 403.

### Pitfall 5: Slug Uniqueness Race Condition

**What goes wrong:** Two concurrent org creation requests with the same name both generate the same slug and both attempt to insert — one fails with a database IntegrityError exposed to the user as a 500.

**Why it happens:** The generate_unique_slug() function checks for existence and generates a slug, but another request slips in between the check and the insert.

**How to avoid:** Add `unique=True` to the slug field at the database level. Wrap org creation in a try/except IntegrityError that retries slug generation. The unique constraint is the safety net; the loop is the fast path.

### Pitfall 6: Forgot Password Reveals Email Existence

**What goes wrong:** The forgot-password endpoint returns different responses for "email found" vs "email not found", allowing enumeration of registered accounts.

**Why it happens:** Developers return a 404 for unknown emails as a natural REST response.

**How to avoid:** Always return 200 with the same message regardless of whether the email exists. The UI-SPEC copy is already correct: "If an account exists for this address, you'll receive a password reset link." — enforce this at the API level too (never return 404 for password reset requests).

### Pitfall 7: shadcn Components Modified Directly in ui/ Directory

**What goes wrong:** The generated files in `components/ui/` are overwritten on the next `npx shadcn add` run, losing customizations.

**Why it happens:** Developers treat the ui/ directory as normal component files and add custom logic directly.

**How to avoid:** Treat `components/ui/` as vendored — never edit directly. Create wrapper components in `components/auth/`, `components/manage/` etc. that import from `components/ui/` and add project-specific logic.

---

## Code Examples

### simplejwt Settings (Security-Correct)

```python
# config/settings/base.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

### Custom User Model (if extending AbstractUser)

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Extends AbstractUser; adds phone and avatar_url for PROF-02."""
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(blank=True)

    # Keep email as the canonical identifier per AUTH-01
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
```

```python
# config/settings/base.py
AUTH_USER_MODEL = 'accounts.User'  # must be set before first migration
```

### Organization + Member Models

```python
# apps/organizations/models.py
import uuid
from django.db import models
from django.conf import settings

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

class OrganizationMember(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('MANAGER', 'Manager'),
        ('VOLUNTEER', 'Volunteer'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')

class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name='venues')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    accessibility_info = models.TextField(blank=True)
    parking_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Zod + react-hook-form Registration Form

```typescript
// lib/schemas/auth.ts
import { z } from 'zod';

export const registerSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

export type RegisterPayload = z.infer<typeof registerSchema>;
```

```tsx
// components/auth/RegisterForm.tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, RegisterPayload } from '@/lib/schemas/auth';
import { Button } from '@/components/ui/button';
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';

export function RegisterForm() {
  const form = useForm<RegisterPayload>({ resolver: zodResolver(registerSchema) });
  const [apiError, setApiError] = useState<string | null>(null);

  const onSubmit = async (data: RegisterPayload) => {
    setApiError(null);
    try {
      await register(data);
      // redirect to /manage on success
    } catch (err) {
      setApiError('An account with this email already exists.');
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        {apiError && (
          <Alert variant="destructive">
            <AlertDescription>{apiError}</AlertDescription>
          </Alert>
        )}
        {/* Fields: first_name, last_name, email, password, confirm_password */}
        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? <Spinner /> : 'Create account'}
        </Button>
      </form>
    </Form>
  );
}
```

### TanStack Query — Org List with Loading/Empty States

```tsx
'use client';
import { useQuery } from '@tanstack/react-query';
import { listOrgs } from '@/lib/api/organizations';
import { Skeleton } from '@/components/ui/skeleton';

export function OrgList() {
  const { data: orgs, isLoading } = useQuery({
    queryKey: ['orgs'],
    queryFn: listOrgs,
  });

  if (isLoading) return <OrgListSkeleton />;     // 3 skeleton cards
  if (!orgs?.length) return <OrgEmptyState />;   // "No organizations yet" + CTA
  return <div>{orgs.map(org => <OrgCard key={org.id} org={org} />)}</div>;
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind config via tailwind.config.js | CSS-native with `@import "tailwindcss"`, no config file | Tailwind v4 (Jan 2025) | Zero config; CSS custom properties native; some third-party component libs lag |
| React Pages Router in Next.js | App Router with Server Components | Next.js 13 (stable in 15+, default in 16) | SSR data fetching without useEffect; layout segments; route groups |
| `dj-rest-auth` / `django-allauth` for auth | simplejwt endpoints directly | Community shift 2023-2024 | Less magic; spec compliance easier; no OAuth overhead for v1 |
| Zod v3 | Zod v4 (current, 4.3.6) | March 2025 | Faster parsing; `z.infer<>` patterns unchanged; `@hookform/resolvers` >=3.x required |
| `axios` in Next.js | Native `fetch` in Server Components; TanStack Query in Client Components | Next.js App Router | Native fetch integrates with Next.js caching; axios doesn't |

**Deprecated / outdated:**
- `djangorestframework-jwt`: unmaintained — use simplejwt
- `dj-rest-auth`: not needed for this spec's auth model
- `moment.js`: use `date-fns` or native `Intl` — not needed in Phase 1 (no datetime display)
- Next.js Pages Router: do not use; App Router is the only supported path going forward

---

## Open Questions

1. **Password reset email delivery in Phase 1**
   - What we know: AUTH-04 and AUTH-05 require password reset via emailed uid/token link. Celery is not yet set up (deferred to Phase 5).
   - What's unclear: Should Phase 1 send password reset emails synchronously (blocking the request) or skip actual email delivery and just return the reset URL for testing purposes?
   - Recommendation: Use Django's synchronous `send_mail()` in Phase 1. Configure `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` in local/development settings so the link appears in the terminal. Switch to real SMTP in production settings (Railway env vars). Celery for async email is a Phase 5 concern.

2. **Invitation flow: user must exist vs. create on invite**
   - What we know: TEAM-01 says "invite a member by email." The spec does not clarify whether the invitee must already have a registered account.
   - What's unclear: Does the invite create an OrganizationMember immediately (requiring the invitee to already be registered), or send an email invitation that creates the membership when accepted?
   - Recommendation: For Phase 1 simplicity, require the invitee to have a registered account. Create the OrganizationMember record immediately on invite. A separate invitation-token flow (with pending state) is more complex and not explicitly required by TEAM-01.

3. **Custom User model vs. AbstractUser extension**
   - What we know: AUTH-01 requires first_name and last_name (both fields exist on AbstractUser). PROF-02 adds phone and avatar_url (custom fields).
   - What's unclear: Whether a full custom User model (AbstractBaseUser) is needed.
   - Recommendation: Extend AbstractUser. It provides email, first_name, last_name, is_active, is_staff, password handling. Add phone and avatar_url as extra fields. Set AUTH_USER_MODEL before the first migration — cannot change later without data migrations.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Backend runtime | Yes | 3.13.11 | — |
| pip | Python package install | Yes | 25.0.1 | — |
| Node.js | Frontend runtime | Yes | 24.13.0 | — |
| npm / npx | Frontend package install | Yes | 11.6.2 | — |
| PostgreSQL (psql CLI) | Database | Yes | 16.11 | — |
| PostgreSQL (server at :5432) | Running DB for tests | Yes | accepting connections | — |
| Docker | Local dev containerization | Yes | 28.0.1 | Use local Postgres |
| git | Version control | Yes | 2.49.0 | — |

**Missing dependencies with no fallback:** None — all Phase 1 dependencies are available.

**Notes:**
- Python 3.13.11 is available. Django 5.2 supports Python 3.10+, so 3.13 is compatible.
- PostgreSQL 16 is available locally and confirmed running at :5432. No SQLite fallback — project policy requires PostgreSQL even in local dev.
- Node 24.13.0 exceeds Next.js 16's minimum requirement (Node 18.17+).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest-django 4.12.0 |
| Config file | backend/pytest.ini (Wave 0 creates this) |
| Quick run command | `pytest apps/accounts/ apps/organizations/ -x -q` |
| Full suite command | `pytest --cov=apps --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | POST /api/v1/auth/register/ creates user, returns 201 | integration | `pytest apps/accounts/tests/test_auth.py::test_register -x` | Wave 0 |
| AUTH-01 | Duplicate email returns 400 | integration | `pytest apps/accounts/tests/test_auth.py::test_register_duplicate_email -x` | Wave 0 |
| AUTH-02 | POST /api/v1/auth/login/ returns access token + sets refresh cookie | integration | `pytest apps/accounts/tests/test_auth.py::test_login -x` | Wave 0 |
| AUTH-03 | POST /api/v1/auth/token/refresh/ with valid cookie returns new access + rotates refresh | integration | `pytest apps/accounts/tests/test_auth.py::test_token_refresh -x` | Wave 0 |
| AUTH-03 | Used refresh token is rejected (blacklist) | integration | `pytest apps/accounts/tests/test_auth.py::test_refresh_token_rotation -x` | Wave 0 |
| AUTH-04 | POST /api/v1/auth/password-reset/ always returns 200 regardless of email existence | integration | `pytest apps/accounts/tests/test_auth.py::test_password_reset_no_enumeration -x` | Wave 0 |
| AUTH-05 | POST /api/v1/auth/password-reset/confirm/ with valid uid+token updates password | integration | `pytest apps/accounts/tests/test_auth.py::test_password_reset_confirm -x` | Wave 0 |
| AUTH-05 | Expired/invalid token returns 400 | integration | `pytest apps/accounts/tests/test_auth.py::test_password_reset_invalid_token -x` | Wave 0 |
| PROF-01 | GET /api/v1/auth/me/ returns user profile | integration | `pytest apps/accounts/tests/test_profile.py::test_get_me -x` | Wave 0 |
| PROF-02 | PATCH /api/v1/auth/me/ updates first_name, last_name, phone, avatar_url | integration | `pytest apps/accounts/tests/test_profile.py::test_update_profile -x` | Wave 0 |
| ORG-01 | POST /api/v1/organizations/ creates org, auto-assigns OWNER | integration | `pytest apps/organizations/tests/test_organizations.py::test_create_org -x` | Wave 0 |
| ORG-02 | GET /api/v1/organizations/ lists only orgs where user is a member | integration | `pytest apps/organizations/tests/test_organizations.py::test_list_orgs -x` | Wave 0 |
| ORG-03 | OWNER can PATCH org; VOLUNTEER gets 403 | integration | `pytest apps/organizations/tests/test_organizations.py::test_update_org_permissions -x` | Wave 0 |
| ORG-04 | Org slug auto-generated; duplicate name gets suffix | unit | `pytest apps/organizations/tests/test_organizations.py::test_slug_generation -x` | Wave 0 |
| TEAM-01 | OWNER/MANAGER can POST invite; VOLUNTEER gets 403 | integration | `pytest apps/organizations/tests/test_team.py::test_invite_member -x` | Wave 0 |
| TEAM-02 | MANAGER cannot invite with role=OWNER | integration | `pytest apps/organizations/tests/test_team.py::test_manager_cannot_invite_owner -x` | Wave 0 |
| TEAM-03 | Any org member can GET team list | integration | `pytest apps/organizations/tests/test_team.py::test_list_members -x` | Wave 0 |
| TEAM-04 | Only OWNER can DELETE member; MANAGER gets 403 | integration | `pytest apps/organizations/tests/test_team.py::test_remove_member_permissions -x` | Wave 0 |
| TEAM-04 | Cross-org: MANAGER from Org B cannot delete Org A member | integration | `pytest apps/organizations/tests/test_team.py::test_cross_org_access_denied -x` | Wave 0 |
| VENU-01 | Org member can POST venue | integration | `pytest apps/organizations/tests/test_venues.py::test_create_venue -x` | Wave 0 |
| VENU-02 | GET venues returns only org's venues | integration | `pytest apps/organizations/tests/test_venues.py::test_list_venues -x` | Wave 0 |
| VENU-03 | Org member can PATCH venue | integration | `pytest apps/organizations/tests/test_venues.py::test_update_venue -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest apps/accounts/ apps/organizations/ -x -q`
- **Per wave merge:** `pytest --cov=apps --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/pytest.ini` — pytest-django configuration (DJANGO_SETTINGS_MODULE)
- [ ] `backend/conftest.py` — shared fixtures (db, authenticated client, UserFactory)
- [ ] `backend/apps/accounts/tests/__init__.py` + `factories.py` — UserFactory
- [ ] `backend/apps/accounts/tests/test_auth.py` — AUTH-01 through AUTH-05 test stubs
- [ ] `backend/apps/accounts/tests/test_profile.py` — PROF-01, PROF-02 test stubs
- [ ] `backend/apps/organizations/tests/__init__.py` + `factories.py` — OrganizationFactory, OrganizationMemberFactory, VenueFactory
- [ ] `backend/apps/organizations/tests/test_organizations.py` — ORG-01 through ORG-04
- [ ] `backend/apps/organizations/tests/test_team.py` — TEAM-01 through TEAM-04 including cross-org access test
- [ ] `backend/apps/organizations/tests/test_venues.py` — VENU-01 through VENU-03

**Frontend testing:** Phase 1 frontend tests are component-level (React Testing Library + vitest) and are out of scope for the Wave 0 gap list — the backend API tests cover all requirement behaviors. Frontend smoke tests (navbar renders, form renders) can be added if vitest is configured as part of the Next.js scaffold.

---

## Project Constraints (from CLAUDE.md)

CLAUDE.md contains GSD workflow enforcement directives. The following apply directly to Phase 1 implementation:

| Directive | Implication for Phase 1 |
|-----------|------------------------|
| Tech stack: Django REST Framework + Next.js + PostgreSQL + Stripe | No deviations; stack is locked |
| Deployment: Vercel (frontend) + Railway (backend + DB) | Settings must support both local dev and Railway env vars; CORS configured for Vercel domain |
| API contract must match TEST_SPEC.md exactly | Endpoint paths, request/response shapes, and status codes are non-negotiable |
| Permission model: OWNER > MANAGER > VOLUNTEER with specific boundaries | All permission logic must implement the exact permission matrix from REQUIREMENTS.md |
| Use GSD workflow entry points (/gsd:execute-phase etc.) | Planner tasks must operate within GSD workflow; no direct edits outside workflow |

**Additional constraints from STATE.md (locked decisions):**
- JWT stored in memory (not localStorage) + HttpOnly cookies for refresh tokens — security baseline is locked
- HMAC-signed QR codes use dedicated QR_SIGNING_KEY env var (not SECRET_KEY) — relevant from Phase 4 onward; establish env var pattern in Phase 1

---

## Sources

### Primary (HIGH confidence)

- STACK.md — verified library versions against PyPI/npm as of 2026-03-28
- ARCHITECTURE.md — Django app structure, service layer pattern, frontend route structure
- PITFALLS.md — JWT storage, DRF object permissions, slug race condition, BLACKLIST_AFTER_ROTATION
- UI-SPEC (01-UI-SPEC.md) — screen contracts, component inventory, color tokens, copy strings — locked by user approval
- REQUIREMENTS.md — AUTH-01 through VENU-03 requirement definitions
- STATE.md — locked decisions: JWT memory storage, HttpOnly cookies, QR_SIGNING_KEY separation

### Secondary (MEDIUM confidence)

- djangorestframework-simplejwt official docs — ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION configuration
- DRF official docs — has_object_permission() calling behavior
- Next.js 16 App Router docs — route groups, Server Components pattern

### Tertiary (LOW confidence)

- shadcn/ui + Tailwind v4 compatibility — confirmed "initialized" per UI-SPEC frontmatter, but full component compatibility should be verified during Wave 0 scaffold

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against PyPI/npm in STACK.md (2026-03-28)
- Architecture: HIGH — patterns from ARCHITECTURE.md; cross-referenced with DRF and Next.js official docs
- Pitfalls: HIGH — sourced from PITFALLS.md which cites official DRF docs, simplejwt docs, and documented CVEs
- UI contracts: HIGH — locked by approved UI-SPEC; no open design decisions remain for Phase 1 screens
- Test map: HIGH — directly derived from REQUIREMENTS.md requirement definitions

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable stack; 30-day validity)
