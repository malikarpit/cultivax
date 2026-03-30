# CultivaX — Frontend Developer Guide

> **Version**: 1.0.0  
> **Last Updated**: March 30, 2026  
> **Author**: Prince

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Getting Started](#4-getting-started)
5. [Routing & Pages](#5-routing--pages)
6. [Component Catalog](#6-component-catalog)
7. [State Management](#7-state-management)
8. [API Integration](#8-api-integration)
9. [Styling System](#9-styling-system)
10. [Accessibility](#10-accessibility)
11. [Responsive Design](#11-responsive-design)
12. [Error Handling](#12-error-handling)

---

## 1. Overview

The CultivaX frontend is a **Next.js 14** application using the **App Router** architecture. It provides:

- **18 pages** covering crop management, service marketplace, admin tools, and more
- **16 reusable components** for consistent UI patterns
- **JWT-based authentication** with protected route wrappers
- **Responsive design** optimized for both desktop and mobile (field use)
- **Accessibility features** including large text and high contrast modes

---

## 2. Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 14.x | React framework with App Router |
| React | 18.x | UI library |
| TypeScript | 5.x | Type safety |
| TailwindCSS | 3.x | Utility-first styling |
| Context API | - | Global state management (auth) |

---

## 3. Project Structure

```
frontend/
├── src/
│   ├── app/                          # App Router pages
│   │   ├── layout.tsx                # Root layout (sidebar + header)
│   │   ├── page.tsx                  # Landing page (redirects to /login)
│   │   ├── globals.css               # Global styles + TailwindCSS imports
│   │   │
│   │   ├── login/
│   │   │   └── page.tsx              # Login page
│   │   ├── register/
│   │   │   └── page.tsx              # Registration page
│   │   │
│   │   ├── dashboard/
│   │   │   └── page.tsx              # Main dashboard with crop cards + stats
│   │   │
│   │   ├── crops/
│   │   │   ├── page.tsx              # Crop list with filters
│   │   │   ├── new/
│   │   │   │   └── page.tsx          # New crop creation form
│   │   │   └── [id]/
│   │   │       ├── page.tsx          # Crop detail (stats + timeline)
│   │   │       ├── log-action/
│   │   │       │   └── page.tsx      # Action logging form
│   │   │       ├── simulate/
│   │   │       │   └── page.tsx      # What-if simulation
│   │   │       └── yield/
│   │   │           └── page.tsx      # Yield submission
│   │   │
│   │   ├── services/
│   │   │   ├── page.tsx              # Service marketplace
│   │   │   ├── request/
│   │   │   │   └── page.tsx          # Service request form
│   │   │   └── review/
│   │   │       └── page.tsx          # Review submission form
│   │   │
│   │   ├── labor/
│   │   │   └── page.tsx              # Labor management
│   │   │
│   │   ├── alerts/
│   │   │   └── page.tsx              # Alerts notification page
│   │   │
│   │   ├── provider/
│   │   │   ├── page.tsx              # Provider dashboard
│   │   │   ├── equipment/
│   │   │   │   └── page.tsx          # Equipment management
│   │   │   └── reviews/
│   │   │       └── page.tsx          # Provider reviews
│   │   │
│   │   └── admin/
│   │       ├── page.tsx              # Admin dashboard
│   │       ├── users/
│   │       │   └── page.tsx          # User management
│   │       ├── providers/
│   │       │   └── page.tsx          # Provider governance
│   │       ├── dead-letters/
│   │       │   └── page.tsx          # Dead letter queue
│   │       ├── health/
│   │       │   └── page.tsx          # System health monitor
│   │       └── templates/
│   │           └── page.tsx          # Crop rule template editor
│   │
│   ├── components/                   # Reusable UI components
│   │   ├── AccessibilityToggle.tsx   # Large text / high contrast switcher
│   │   ├── ActionForm.tsx            # Action logging form
│   │   ├── ActionLogList.tsx         # Action log timeline display
│   │   ├── AlertBanner.tsx           # System alert banner with severity
│   │   ├── CropCard.tsx              # Crop summary card for dashboard
│   │   ├── CropForm.tsx              # Crop creation/edit form
│   │   ├── CropTimeline.tsx          # Visual timeline of crop actions
│   │   ├── DashboardStats.tsx        # Dashboard statistics widgets
│   │   ├── DataTable.tsx             # Generic sortable data table
│   │   ├── Header.tsx                # Top navigation header
│   │   ├── ProtectedRoute.tsx        # Auth guard wrapper
│   │   ├── ProviderCard.tsx          # Service provider card
│   │   ├── Sidebar.tsx               # Side navigation menu
│   │   ├── SimulationResult.tsx      # What-if simulation results display
│   │   ├── StatsWidget.tsx           # Individual stat widget
│   │   └── YieldForm.tsx             # Harvest yield submission form
│   │
│   ├── context/
│   │   └── AuthContext.tsx           # Authentication context provider
│   │
│   ├── hooks/
│   │   ├── useApi.ts                 # API call hook with error handling
│   │   └── useAccessibility.ts       # Accessibility settings hook
│   │
│   └── lib/
│       ├── api.ts                    # API client with base URL + auth headers
│       └── auth.ts                   # Auth utility functions
│
├── public/                           # Static assets
├── package.json                      # Dependencies + scripts
├── tsconfig.json                     # TypeScript configuration
├── tailwind.config.ts                # TailwindCSS configuration
├── next.config.js                    # Next.js configuration
└── postcss.config.js                 # PostCSS configuration
```

---

## 4. Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend running at `http://localhost:8000`

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Available Scripts

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `npm run dev` | Start development server with hot reload |
| `build` | `npm run build` | Build for production |
| `start` | `npm start` | Start production server |
| `lint` | `npm run lint` | Run ESLint |

---

## 5. Routing & Pages

### Page Map

The application uses Next.js App Router with the following page hierarchy:

| Route | Page | Auth | Role | Description |
|-------|------|------|------|-------------|
| `/` | Landing | ❌ | — | Redirects to `/login` |
| `/login` | Login | ❌ | — | JWT authentication form |
| `/register` | Register | ❌ | — | User registration form |
| `/dashboard` | Dashboard | ✅ | all | Main overview with crop cards + stats |
| `/crops` | Crop List | ✅ | farmer | Filterable crop instance list |
| `/crops/new` | New Crop | ✅ | farmer | Crop creation form |
| `/crops/[id]` | Crop Detail | ✅ | farmer | Stats grid, timeline, action log |
| `/crops/[id]/log-action` | Log Action | ✅ | farmer | Action logging form |
| `/crops/[id]/simulate` | Simulate | ✅ | farmer | What-if simulation UI |
| `/crops/[id]/yield` | Yield | ✅ | farmer | Harvest yield entry |
| `/services` | Marketplace | ✅ | all | Service provider browsing |
| `/services/request` | Request | ✅ | farmer | Service request form |
| `/services/review` | Review | ✅ | farmer | Service review form |
| `/labor` | Labor | ✅ | all | Labor management |
| `/alerts` | Alerts | ✅ | all | Notification list |
| `/provider` | Provider | ✅ | provider | Provider dashboard |
| `/provider/equipment` | Equipment | ✅ | provider | Equipment management |
| `/provider/reviews` | Reviews | ✅ | provider | View received reviews |
| `/admin` | Admin | ✅ | admin | Admin dashboard with stats |
| `/admin/users` | Users | ✅ | admin | User CRUD management |
| `/admin/providers` | Providers | ✅ | admin | Provider governance |
| `/admin/dead-letters` | Dead Letters | ✅ | admin | Failed event queue viewer |
| `/admin/health` | Health | ✅ | admin | System health monitor |
| `/admin/templates` | Templates | ✅ | admin | Crop rule template editor |

### Layout Structure

The root `layout.tsx` wraps all pages with:

```
┌─────────────────────────────────────────────┐
│  Header (notifications, user menu, a11y)     │
├─────────┬───────────────────────────────────┤
│         │                                    │
│ Sidebar │         Page Content               │
│ (nav)   │         (children)                 │
│         │                                    │
│         │                                    │
│         │                                    │
└─────────┴───────────────────────────────────┘
```

The sidebar and header are hidden on `/login` and `/register` pages.

---

## 6. Component Catalog

### Core Layout Components

#### `Sidebar` — Main navigation menu

**Props**: None (reads auth context for role-based menu)

**Navigation Items by Role:**

| Role | Menu Items |
|------|-----------|
| farmer | Dashboard, My Crops, Services, Labor, Alerts |
| provider | Dashboard, My Services, Equipment, Reviews |
| admin | Dashboard, Users, Providers, Health, Dead Letters, Templates |

#### `Header` — Top navigation bar

**Props**: None (reads auth context)

**Features:**
- User name and role display
- Notification bell with unread count
- Accessibility toggle
- Logout button

---

### Crop Components

#### `CropCard` — Crop summary card

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `crop` | `CropInstance` | Crop data object |
| `onClick` | `() => void` | Navigation handler |

Displays: crop type icon, variety, current state badge, sowing date, stress score indicator.

#### `CropForm` — Crop creation/edit form

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `onSubmit` | `(data) => void` | Form submission handler |
| `initialData` | `CropInstance?` | Pre-fill for editing |

**Fields:** crop type (select), variety, sowing date, field area, region, notes.

#### `CropTimeline` — Visual timeline of crop actions

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `actions` | `ActionLog[]` | Ordered action list |
| `sowingDate` | `string` | Crop sowing date |

Renders a vertical timeline with action type icons, dates, and details.

#### `ActionForm` — Action logging form

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `cropId` | `string` | Target crop ID |
| `onSubmit` | `(data) => void` | Submission handler |

**Fields:** action type, effective date, quantity, unit, notes.

#### `ActionLogList` — Tabular action log display

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `actions` | `ActionLog[]` | Action log entries |

#### `SimulationResult` — What-if results display

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `result` | `SimulationOutput` | Simulation response data |

Displays: stress delta (with color coding), risk delta, projected stage, warnings.

#### `YieldForm` — Harvest yield submission form

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `cropId` | `string` | Target crop ID |
| `onSubmit` | `(data) => void` | Submission handler |

**Fields:** actual yield (kg), harvest date, quality grade, notes.

---

### Dashboard Components

#### `DashboardStats` — Statistics grid widget

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `stats` | `DashboardStatData` | Statistics data |

Displays summary cards: total crops, active crops, average stress, pending requests.

#### `StatsWidget` — Individual stat display

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `label` | `string` | Stat label |
| `value` | `string | number` | Stat value |
| `trend` | `'up' | 'down' | 'neutral'` | Trend indicator |

---

### Service Components

#### `ProviderCard` — Service provider card

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `provider` | `ServiceProvider` | Provider data |
| `onRequest` | `() => void` | Request service handler |

Displays: business name, service type, trust score (star rating), service area, hourly rate.

---

### Utility Components

#### `DataTable` — Generic sortable table

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `columns` | `Column[]` | Column definitions |
| `data` | `any[]` | Row data |
| `sortable` | `boolean` | Enable column sorting |

#### `AlertBanner` — System alert display

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `alert` | `Alert` | Alert data |
| `onDismiss` | `() => void` | Dismiss handler |

Color-coded by severity: info (blue), warning (yellow), critical (red).

#### `ProtectedRoute` — Auth guard wrapper

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `children` | `ReactNode` | Protected content |
| `requiredRole` | `string?` | Required user role |

Redirects to `/login` if not authenticated. Shows 403 if role doesn't match.

#### `AccessibilityToggle` — Accessibility settings

**Props**: None (uses `useAccessibility` hook)

**Features:**
- Large text mode (scales base font size)
- High contrast mode (enhanced color contrast ratios)
- Settings persisted in localStorage

---

## 7. State Management

### Authentication Context

The `AuthContext` provides global authentication state:

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (phone: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}
```

**Usage:**

```tsx
import { useAuth } from '@/context/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();
  // ...
}
```

**Token Storage:** JWT tokens are stored in `localStorage` with keys:
- `cultivax_access_token`
- `cultivax_refresh_token`
- `cultivax_user`

---

## 8. API Integration

### API Client (`lib/api.ts`)

The API client provides a configured `fetch` wrapper:

```typescript
import { api } from '@/lib/api';

// GET request
const crops = await api.get('/crops/?page=1&per_page=20');

// POST request
const newCrop = await api.post('/crops/', {
  crop_type: 'wheat',
  sowing_date: '2026-03-15',
  region: 'haryana',
});

// PUT request
await api.put(`/crops/${cropId}`, updateData);
```

**Features:**
- Automatic `Authorization: Bearer <token>` header injection
- Base URL from `NEXT_PUBLIC_API_URL` environment variable
- JSON content type headers
- Error response parsing

### useApi Hook

The `useApi` hook provides loading/error state management:

```typescript
import { useApi } from '@/hooks/useApi';

function CropList() {
  const { data, loading, error, execute } = useApi();

  useEffect(() => {
    execute('GET', '/crops/');
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage message={error} />;
  return <CropGrid crops={data.items} />;
}
```

---

## 9. Styling System

### TailwindCSS Configuration

The project uses TailwindCSS with a custom configuration:

**Color Palette:**

| Color | Usage | Hex |
|-------|-------|-----|
| Primary (green) | Actions, active states | `#16a34a` |
| Secondary (blue) | Links, info | `#2563eb` |
| Accent (amber) | Warnings, highlights | `#d97706` |
| Danger (red) | Errors, critical alerts | `#dc2626` |
| Neutral (gray) | Backgrounds, borders | `#6b7280` |

**Breakpoints:**

| Breakpoint | Min Width | Use Case |
|-----------|-----------|----------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Large desktop |

### Global Styles (`globals.css`)

Defines:
- CSS custom properties for theme colors
- Base typography (font family, sizes)
- Scrollbar styling
- Loading spinner animation
- High contrast mode overrides
- Large text mode scaling

---

## 10. Accessibility

### Features

| Feature | Implementation |
|---------|---------------|
| **Large Text Mode** | Increases base font size by 25% via CSS variable |
| **High Contrast Mode** | Enhances color contrast ratios, adds borders to cards |
| **Keyboard Navigation** | All interactive elements are tab-focusable |
| **ARIA Labels** | Form inputs have associated labels |
| **Focus Indicators** | Visible focus rings on all interactive elements |
| **Color Semantics** | Status information is never conveyed by color alone |

### useAccessibility Hook

```typescript
const { largeText, highContrast, toggleLargeText, toggleHighContrast } = useAccessibility();
```

Settings persist across sessions via `localStorage`.

---

## 11. Responsive Design

### Layout Behavior

| Viewport | Sidebar | Header | Content |
|----------|---------|--------|---------|
| Desktop (≥1024px) | Fixed left panel | Full width | Main area with gap |
| Tablet (768–1023px) | Collapsible overlay | Full width | Full width |
| Mobile (<768px) | Hidden (hamburger menu) | Compact | Full width, stacked cards |

### Component Responsiveness

- **CropCard**: Grid → 3 cols (desktop), 2 cols (tablet), 1 col (mobile)
- **DataTable**: Horizontal scroll on small screens
- **DashboardStats**: 4 cols → 2 cols → 1 col
- **Forms**: Single column layout on all sizes
- **Sidebar**: Fixed → overlay → hamburger menu

---

## 12. Error Handling

### API Errors

All API calls handle errors through a consistent pattern:

```typescript
try {
  const data = await api.post('/crops/', formData);
  router.push(`/crops/${data.id}`);
} catch (error) {
  if (error.status === 401) {
    logout();
    router.push('/login');
  } else if (error.status === 422) {
    setFieldErrors(error.detail);
  } else {
    setGlobalError('Something went wrong. Please try again.');
  }
}
```

### Error States

Every data-fetching page handles three states:

1. **Loading**: Skeleton loaders or spinner
2. **Error**: Error message with retry button
3. **Empty**: "No data" message with call-to-action

### Toast Notifications

Success/error feedback uses toast notifications:
- **Success** (green): "Crop created successfully"
- **Error** (red): "Failed to submit yield"
- **Warning** (yellow): "Offline mode — changes will sync later"

---

## Appendix A: TypeScript Types

### Core Types

```typescript
interface User {
  id: string;
  full_name: string;
  phone: string;
  email?: string;
  role: 'farmer' | 'provider' | 'admin';
  region?: string;
  is_active: boolean;
  created_at: string;
}

interface CropInstance {
  id: string;
  farmer_id: string;
  crop_type: string;
  variety?: string;
  sowing_date: string;
  state: 'created' | 'active' | 'harvested' | 'closed';
  current_day_number: number;
  current_growth_stage: string;
  stress_score: number;
  risk_index: number;
  field_area_acres?: number;
  region: string;
  seasonal_window_category: string;
  created_at: string;
  updated_at: string;
}

interface ActionLog {
  id: string;
  crop_instance_id: string;
  action_type: string;
  effective_date: string;
  quantity?: number;
  unit?: string;
  notes?: string;
  created_at: string;
}

interface ServiceProvider {
  id: string;
  user_id: string;
  business_name: string;
  service_type: string;
  description?: string;
  service_area: string;
  trust_score: number;
  hourly_rate?: number;
  is_verified: boolean;
}

interface Alert {
  id: string;
  user_id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}
```

## Appendix B: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | `http://localhost:8000` | Backend API base URL |

## Appendix C: Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |
| Mobile Chrome | 90+ |
| Mobile Safari | 14+ |
