# CultivaX — Frontend UI Specification

> **Purpose:** Complete UI/UX reference for Figma/Stitch design and frontend implementation.
> Covers every route, page layout, interactive element, component state, design tokens, and animation spec.

---

## Table of Contents

1. [Design System & Tokens](#1-design-system--tokens)
2. [Global Layout & Navigation](#2-global-layout--navigation)
3. [Component Library](#3-component-library)
4. [Page Specifications](#4-page-specifications)
5. [Animation & Motion System](#5-animation--motion-system)
6. [Notification System](#6-notification-system)
7. [Accessibility & i18n](#7-accessibility--i18n)
8. [Responsive Breakpoints](#8-responsive-breakpoints)

---

## 1. Design System & Tokens

### 1.1 Theme Modes

| Property | Dark Mode | Light Mode |
|----------|-----------|------------|
| Background (Primary) | `#0B1120` | `#F7F8FA` |
| Background (Secondary) | `#111827` | `#FFFFFF` |
| Surface / Cards | `#1A2332` | `#FFFFFF` |
| Surface Hover | `#1F2B3D` | `#F3F4F6` |
| Border | `#2A3548` | `#E5E7EB` |
| Border (Subtle) | `#1E293B` | `#F0F0F0` |
| Text (Primary) | `#F1F5F9` | `#111827` |
| Text (Secondary) | `#94A3B8` | `#6B7280` |
| Text (Muted) | `#64748B` | `#9CA3AF` |

> **Rule:** Use dark gray (`#0B1120`) NOT pure black. Use off-white (`#F1F5F9`) NOT pure white.
> Toggle persisted in `user.accessibility_settings.theme` JSONB field.

### 1.2 Color Palette

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-primary` | `#34D399` (Emerald 400) | Primary CTA, active states, links |
| `--color-primary-hover` | `#10B981` | Button hover |
| `--color-primary-muted` | `#34D399/15%` | Tinted backgrounds |
| `--color-accent` | `#F59E0B` (Amber 500) | CultivaX "X", highlights, badges |
| `--color-accent-warm` | `#F97316` | Urgent indicators |
| `--color-danger` | `#EF4444` | Error, risk-critical, delete |
| `--color-danger-muted` | `#EF4444/10%` | Risk background tint |
| `--color-warning` | `#FBBF24` | Warnings, at-risk states |
| `--color-info` | `#3B82F6` | Informational, links, info badges |
| `--color-success` | `#22C55E` | Success confirmation |
| `--color-frost` | `rgba(255,255,255,0.06)` | Frosted glass overlay (dark) |
| `--color-frost-light` | `rgba(0,0,0,0.03)` | Frosted glass overlay (light) |

### 1.3 Typography

| Token | Font | Weight | Size | Line Height |
|-------|------|--------|------|-------------|
| `--text-display` | Inter | 700 | 36px | 1.2 |
| `--text-h1` | Inter | 700 | 28px | 1.3 |
| `--text-h2` | Inter | 600 | 22px | 1.3 |
| `--text-h3` | Inter | 600 | 18px | 1.4 |
| `--text-body` | Inter | 400 | 15px | 1.6 |
| `--text-body-sm` | Inter | 400 | 13px | 1.5 |
| `--text-caption` | Inter | 500 | 11px | 1.4 |
| `--text-mono` | JetBrains Mono | 400 | 13px | 1.5 |

> **Google Fonts:** `Inter:wght@400;500;600;700` + `JetBrains+Mono:wght@400`
> 
> **Large Text Mode (MSDD 7.1):** Multiply all sizes by `1.5×`. Store toggle in `accessibility_settings.largeText`.

### 1.4 Spacing Scale

| Token | Value |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |
| `--space-16` | 64px |

### 1.5 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Inputs, small badges |
| `--radius-md` | 10px | Cards, dropdowns |
| `--radius-lg` | 16px | Modals, panels |
| `--radius-xl` | 24px | Large feature cards, landing hero |
| `--radius-full` | 9999px | Avatars, pills, toggles |

### 1.6 Elevation / Shadow

| Token | Dark Mode | Light Mode |
|-------|-----------|------------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` | `0 1px 2px rgba(0,0,0,0.05)` |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.4)` | `0 4px 12px rgba(0,0,0,0.08)` |
| `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.5)` | `0 8px 24px rgba(0,0,0,0.12)` |
| `--shadow-glow` | `0 0 20px rgba(52,211,153,0.15)` | `0 0 20px rgba(52,211,153,0.08)` |
| `--shadow-hover` | `0 8px 30px rgba(0,0,0,0.5)` | `0 8px 30px rgba(0,0,0,0.15)` |

### 1.7 Glassmorphism / Frost Tokens

```css
.frost-card {
  background: var(--color-frost);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-md);
}

.frost-card-tinted {
  background: linear-gradient(
    135deg,
    rgba(52,211,153,0.08) 0%,
    rgba(245,158,11,0.04) 100%
  );
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(52,211,153,0.12);
}
```

---

## 2. Global Layout & Navigation

### 2.1 Layout Structure

```
┌─────────────────────────────────────────────────────┐
│                  TOP HEADER BAR                       │
│  [☰/Stacks] Logo    Search     🔔 Notifications  👤  │
├──────────┬──────────────────────────────────────────┤
│          │                                           │
│  SIDE    │         MAIN CONTENT AREA                 │
│  BAR     │                                           │
│          │                                           │
│  (colla- │                                           │
│  psible) │                                           │
│          │                                           │
│          │                                           │
│          │                                           │
│          │                                           │
└──────────┴──────────────────────────────────────────┘
```

### 2.2 Top Header Bar

| Element | Position | Description | States |
|---------|----------|-------------|--------|
| Logo | Left | "CultivaX" text mark — clickable → `/dashboard` | — |
| Sidebar Toggle | Left (beside logo) | Collapse/expand sidebar icon | Expanded / Collapsed |
| Search | Center | Frosted input, searches crops, providers, actions | Empty / Typing / Results dropdown |
| Theme Toggle | Right | Sun/Moon icon, switches dark ↔ light | Dark / Light |
| Notification Bell | Right | Bell icon with red badge count | Default / Has unread (badge) / Dropdown open |
| User Avatar | Right | Circular avatar + dropdown (Profile, Settings, Accessibility, Logout) | Default / Dropdown open |

**Header Style:**
```css
.top-header {
  height: 56px;
  background: var(--color-frost);
  backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 50;
}
```

### 2.3 Sidebar Navigation

**Width:** 240px expanded → 64px collapsed (icon-only mode).

**Sections (by role):**

#### Farmer Sidebar
| Icon | Label | Route | Badge |
|------|-------|-------|-------|
| 🏠 Home | Dashboard | `/dashboard` | — |
| 🌾 Crops | My Crops | `/crops` | Count of active |
| 📋 Actions | Log Action | `/crops/[id]/log-action` | — |
| 🔮 Simulate | What-If | `/crops/[id]/simulate` | — |
| 🏪 Services | Marketplace | `/services` | — |
| 🔔 Alerts | Notifications | `/alerts` | Unread count |
| 👷 Labor | Labor | `/labor` | — |

#### Provider Sidebar (prepended)
| Icon | Label | Route |
|------|-------|-------|
| 📋 Requests | Provider Home | `/provider` |
| 🚜 Equipment | My Equipment | `/provider/equipment` |
| ⭐ Reviews | My Reviews | `/provider/reviews` |

#### Admin Sidebar (appended)
| Icon | Label | Route |
|------|-------|-------|
| ⚙️ Admin | Admin Panel | `/admin` |
| 👤 Users | User Mgmt | `/admin/users` |
| 🏪 Providers | Provider Mgmt | `/admin/providers` |
| 📐 Templates | Rule Templates | `/admin/templates` |
| 💚 Health | System Health | `/admin/health` |
| 📭 Dead Letters | DLQ | `/admin/dead-letters` |

**Sidebar Behavior:**
- **Collapsed mode:** Show only icons, tooltip on hover shows label.
- **Pinned mode:** User can pin via accessibility menu → sidebar stays expanded always.
- **Mobile:** Sidebar hidden by default. Shown via **stacks icon** (agriculture-themed ☰ replacement — 3 horizontal lines styled as crop rows / soil layers).
- **Active state:** Left `3px` accent border + tinted background + bold text.

**Sidebar Style:**
```css
.sidebar {
  background: var(--surface);
  border-right: 1px solid var(--border);
  transition: width 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar-item.active {
  background: var(--color-primary-muted);
  border-left: 3px solid var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}
```

### 2.4 Mobile Navigation (Alternative)

**Consideration:** Floating frosted bottom nav bar (to be decided by user).

```
┌─────────────────────────────────────┐
│   Page Content                       │
│                                      │
│                                      │
│                                      │
│   ┌───────────────────────────────┐  │
│   │  🏠   🌾   🏪   🔔   👤     │  │ ← Floating frosted bottom bar
│   └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Specs:**
- `backdrop-filter: blur(20px)`
- Fixed bottom, `16px` margin from edges
- `border-radius: var(--radius-xl)`
- 5 items max (Dashboard, Crops, Services, Alerts, Profile)
- Active icon gets `--color-primary` fill + dot indicator below

---

## 3. Component Library

### 3.1 Icon System

**Primary Library:** [Lucide Icons](https://lucide.dev/) — consistent stroke-based, 24×24 default.

| Category | Icons to Use |
|----------|-------------|
| Navigation | `Home`, `Sprout`, `Store`, `Bell`, `Shield`, `Settings`, `ChevronDown` |
| Crops | `Wheat`, `Leaf`, `TreePine`, `Flower2`, `Sun`, `CloudRain` |
| Actions | `Plus`, `Edit`, `Trash2`, `Check`, `X`, `RotateCw`, `Upload` |
| Data | `BarChart3`, `LineChart`, `PieChart`, `TrendingUp`, `TrendingDown` |
| Status | `AlertTriangle`, `AlertCircle`, `CheckCircle`, `Clock`, `Loader2` |
| Users | `User`, `Users`, `UserCheck`, `UserX`, `ShieldCheck` |
| System | `Search`, `Menu`, `Moon`, `Sun`, `Monitor`, `Palette` |

**Custom SVG Fallback:** Any icon can be replaced with a custom SVG via `<IconWrapper>` component.
**Emoji support:** Optional emoji display alongside icons for agricultural warmth.

### 3.2 Buttons

| Variant | Background | Text | Border | Usage |
|---------|-----------|------|--------|-------|
| Primary | `var(--color-primary)` | White | None | Main CTA (Save, Submit, Create) |
| Secondary | Transparent | `var(--color-primary)` | `1px solid var(--color-primary)` | Secondary actions |
| Ghost | Transparent | `var(--text-secondary)` | None | Tertiary, navigation |
| Danger | `var(--color-danger)` | White | None | Delete, terminate, destructive |
| Icon | Transparent | `var(--text-secondary)` | None | Icon-only actions |

**States (ALL buttons):**
| State | Effect |
|-------|--------|
| Default | Base styles |
| Hover | Brightness +10%, shadow-sm |
| Active/Pressed | Scale(0.97), brightness -5% |
| Disabled | Opacity 0.5, cursor: not-allowed |
| Loading | Spinner replaces text, disabled state |

**Sizes:**
| Size | Height | Padding | Font |
|------|--------|---------|------|
| `sm` | 32px | 12px 16px | 13px |
| `md` | 40px | 12px 20px | 15px |
| `lg` | 48px | 14px 24px | 16px |

### 3.3 Input Fields

**Base Style:**
```css
.input {
  height: 44px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 15px;
  transition: border-color 200ms, box-shadow 200ms;
}
.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
  outline: none;
}
.input.error {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 3px var(--color-danger-muted);
}
```

**Variants:**
| Type | Notes |
|------|-------|
| Text input | Standard single-line |
| Textarea | Auto-growing, min 3 rows |
| Select / Dropdown | Custom styled, frosted dropdown panel |
| Date picker | Calendar popup with frosted overlay |
| Search input | Left search icon, right clear button |
| Number input | Stepper arrows or inline +/- |
| Phone input | Country code prefix + number |

### 3.4 Cards

| Variant | Style | Usage |
|---------|-------|-------|
| Frost Card | `frost-card` class, blur background | Default card everywhere |
| Frost Card Tinted | Green/amber gradient frost | Feature highlights, dashboard stats |
| Stat Card | Frost + large number + icon + label | Dashboard KPIs |
| Crop Card | Frost + crop icon + state badge + stress ring | Crop list grid |
| Provider Card | Frost + avatar + trust score ring + CTA | Marketplace |
| Alert Card | Frost + severity color left border | Alert list |
| Admin Card | Frost + icon + nav link | Admin home grid |

**All cards must have:**
- Hover lift animation (translateY -2px, shadow increase)
- `border-radius: var(--radius-md)`
- Consistent padding `var(--space-5)` or `var(--space-6)`

### 3.5 Badges / Pills

| Variant | Background | Text Color | Usage |
|---------|-----------|------------|-------|
| State: Active | `#22C55E/15%` | `#22C55E` | Crop state |
| State: AtRisk | `#EF4444/15%` | `#EF4444` | Crop state |
| State: Delayed | `#FBBF24/15%` | `#FBBF24` | Crop state |
| State: Harvested | `#A78BFA/15%` | `#A78BFA` | Crop state |
| State: Created | `#3B82F6/15%` | `#3B82F6` | Crop state |
| State: Closed | `#6B7280/15%` | `#6B7280` | Crop state |
| Severity: Critical | `#EF4444/15%` | `#EF4444` | Alert severity |
| Severity: High | `#F97316/15%` | `#F97316` | Alert severity |
| Severity: Medium | `#FBBF24/15%` | `#FBBF24` | Alert severity |
| Severity: Low | `#3B82F6/15%` | `#3B82F6` | Alert severity |
| Trust Score | Dynamic (green→red gradient) | White | Provider trust |
| Role | Primary muted | Primary | User role |
| Count | `--color-danger` solid | White | Notification count |

**Style:** `border-radius: var(--radius-full)`, `padding: 4px 12px`, `font-size: 12px`, `font-weight: 600`.

### 3.6 Tabs

**Style:** Underline tabs with frosted background option.

```
  ┌─────────┬──────────┬───────────┬──────────┐
  │Overview │ Actions  │ Analytics │ Simulate │
  └─────────┴──────────┴───────────┴──────────┘
       ▔▔▔▔▔▔▔▔                                  ← Active indicator (--color-primary, 2px)
```

| State | Text | Indicator |
|-------|------|-----------|
| Default | `--text-muted` | None |
| Hover | `--text-secondary` | Subtle underline |
| Active | `--color-primary`, weight 600 | 2px solid `--color-primary` bottom |

**Variants:**
1. **Underline tabs** (default for page tabs)
2. **Pill tabs** — frosted pill background for active, used for chart toggle (Pie / Bar / Line)
3. **Segmented control** — for binary toggles (Card / Table view)

### 3.7 Toggle Switches

| Size | Width | Height | Usage |
|------|-------|--------|-------|
| `sm` | 36px | 20px | Compact settings |
| `md` | 44px | 24px | Default |
| `lg` | 52px | 28px | Accessibility panel |

**Colors:**
| State | Track | Thumb |
|-------|-------|-------|
| Off | `var(--border)` | White |
| On | `var(--color-primary)` | White |
| Disabled | `var(--border)` opacity 50% | Gray |

### 3.8 Progress Ring

**Purpose:** Visualize 0-1 probabilistic values (stress score, risk index, trust score).

```
     ╭───────╮
    │  0.82  │    ← Animated count-up number
    │  Risk  │    ← Label below
     ╰───────╯
    [████████░░]   ← Ring arc (filled = value)
```

| Property | Spec |
|----------|------|
| Size | 64px (sm), 96px (md), 128px (lg) |
| Stroke width | 6px |
| Background track | `var(--border)` |
| Fill color | Dynamic: Green (0-0.3) → Yellow (0.3-0.6) → Red (0.6-1.0) |
| Animation | Animate stroke-dashoffset on mount |
| Center | Count-up number + label |

### 3.9 Charts

**Library:** Recharts (React) or Chart.js.

**Chart Toggle:** Pill tabs above chart → Line (default) | Bar | Pie.

| Chart Type | Usage |
|-----------|-------|
| Line | Stress trend over time, risk trend, weather forecast |
| Bar | Yield comparison, regional clusters, action frequency |
| Pie / Donut | Crop distribution by type/state, service type breakdown |

**Chart Colors (consistent palette):**
```
['#34D399', '#F59E0B', '#3B82F6', '#A78BFA', '#EF4444', '#EC4899']
```

**Chart Style:**
- Background: transparent (inherits card frost)
- Grid lines: `var(--border)` with 0.3 opacity
- Tooltip: Frosted card style
- Legend: Inline below chart, pill badges

### 3.10 Map Component

**Library:** React Leaflet or Mapbox GL JS.

| Feature | Description |
|---------|-------------|
| Default view | User's region, zoom level 8 |
| Markers | Crop locations, color-coded by state (green/yellow/red) |
| Clusters | Group nearby crops into cluster circles |
| Popup | Crop card summary on marker click |
| Weather overlay | Toggle-able weather layer (temperature/rainfall) |
| Satellite toggle | Switch between map and satellite view |

### 3.11 Data Table

**Used in:** Admin pages, crop list (table view toggle), alerts list.

| Feature | Spec |
|---------|------|
| Header row | Sticky, frosted background, sortable columns (▲▼ icons) |
| Row hover | Background `var(--surface-hover)` |
| Pagination | Bottom bar: "Showing 1-20 of 156" + page buttons |
| Column resize | Draggable column dividers |
| Bulk select | Checkbox column + bulk action toolbar |
| Empty state | Centered illustration + message |
| Search/Filter | Inline filter row below header |

### 3.12 Skeleton Loaders

**Style:** Shimmer effect (gradient sweep), NOT gray boxes.

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface) 25%,
    var(--surface-hover) 50%,
    var(--surface) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}
```

**Skeleton variants for each page:**
- Dashboard: 4 stat card skeletons + 6 crop card skeletons
- Crop list: Grid of card skeletons
- Crop detail: Header skeleton + 4 stat skeletons + timeline skeleton
- Admin table: Row skeletons with alternating widths

### 3.13 Empty States

Each empty state has: illustration/icon (from Lucide) + title + subtitle + CTA button.

| Page | Icon | Title | CTA |
|------|------|-------|-----|
| Crops (empty) | `Sprout` (lg) | "No crops yet" | "+ Add Your First Crop" |
| Alerts (empty) | `BellOff` (lg) | "All caught up!" | "View acknowledged alerts" |
| Services (no results) | `SearchX` | "No providers found" | "Clear filters" |
| Provider requests | `Inbox` (lg) | "No pending requests" | — |

---

## 4. Page Specifications

### 4.0 Landing Page (Public)

**Route:** `/` (unauthenticated)
**Concept:** Apple-inspired, frosted glassmorphism, full-screen sections.

#### Sections

| # | Section | Description | Elements |
|---|---------|-------------|----------|
| 1 | **Hero** | Full-viewport, gradient mesh background (dark emerald → navy). Large headline: "Intelligent Crop Management for Everyone." Subtitle. Two CTAs. | `[Get Started ▸]` primary, `[See How It Works]` ghost. Floating frosted crop illustration. |
| 2 | **Stats Bar** | Horizontal strip with animated count-up numbers | "10,000+ Farmers" · "3 Indian States" · "95% Uptime" · "Real-time Intelligence" |
| 3 | **Features** | Bento grid of 6 feature tiles (frosted + tinted) | Each tile: icon + title + 1-line description. Tiles for: Crop Timeline, Smart Alerts, What-If Simulation, Service Marketplace, ML Intelligence, Multi-Language |
| 4 | **For Everyone** | 3-column cards — Farmer / Provider / Admin | Each card: role icon, 3 bullet features, CTA → Register |
| 5 | **How It Works** | 4-step horizontal timeline with frosted step cards | Step 1: Register → Step 2: Add Crop → Step 3: Monitor → Step 4: Harvest |
| 6 | **Testimonials** | Carousel of frosted quote cards | Photo + name + region + quote |
| 7 | **Contact & Support** | Frosted form card + info grid | Email input + message textarea + Send button. Support hours, phone, email. |
| 8 | **Footer** | Dark section with links | Logo, nav links (Features, About, Contact, Privacy), social icons |

**Navigation (Landing only):** Floating frosted top bar with: Logo | Features | For Everyone | Contact | `[Login]` ghost | `[Get Started ▸]` primary.

---

### 4.1 Login Page

**Route:** `/login`

| Element | Type | Spec |
|---------|------|------|
| Logo | Text | "CultivaX" — green + amber |
| Subtitle | Text | "Sign in to your account" |
| Phone input | Input (tel) | Label: "Phone Number", placeholder |
| Password input | Input (password) | Label: "Password", eye toggle to show/hide |
| Remember me | Checkbox | "Remember me" — persists token |
| Sign In | Button (primary, full-width) | Loading spinner state |
| Register link | Link | "Don't have an account? Register" |
| Error banner | Inline banner | Red tinted, shown on failure |

**Background:** Gradient mesh or subtle animated grain.

---

### 4.2 Register Page

**Route:** `/register`

| Element | Type |
|---------|------|
| Logo + subtitle | Text: "Create your account" |
| Full Name | Input (text) |
| Phone Number | Input (tel) |
| Email | Input (email), labeled "(Optional)" |
| Region | Dropdown select: Indian states list |
| Role | Segmented control: Farmer / Service Provider |
| Password | Input (password) with strength indicator bar |
| Confirm Password | Input (password) with match indicator |
| Create Account | Button (primary, full-width) |
| Login link | "Already have an account? Sign In" |
| Error banner | Inline banner |

---

### 4.3 Dashboard (Farmer)

**Route:** `/dashboard`

```
┌─────────────────────────────────────────────────────────┐
│ Welcome back, [Name]                                     │
│ Here's your farm overview        [Quick Actions ▾]       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│  │Active│ │Stress│ │ Avg  │ │Booked│  ← Stat Cards      │
│  │Crops │ │Alerts│ │ Risk │ │Servic│    (frost-tinted)   │
│  │  12  │ │   3  │ │ 24%  │ │   5  │    count-up anim   │
│  └──────┘ └──────┘ └──────┘ └──────┘                    │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────┐          │
│  │  Weather Forecast  │  │  Crop Health Trend  │         │
│  │  ☀️ 32°C Sunny     │  │  [Line|Bar|Pie]     │         │
│  │  5-day forecast    │  │  ╱╲_╱╲__            │         │
│  └────────────────────┘  └────────────────────┘          │
│                                                          │
│  ┌────────────────────────────────────────────┐          │
│  │  Map View                          [📍]    │          │
│  │  ┌──────────────────────────────────────┐  │          │
│  │  │        Interactive Map               │  │          │
│  │  │   🟢  🟢  🟡  🔴                    │  │          │
│  │  └──────────────────────────────────────┘  │          │
│  └────────────────────────────────────────────┘          │
│                                                          │
│  Alert Banner (if pending)                    [Dismiss]  │
│                                                          │
│  Your Crops                           [+ New Crop]       │
│  ┌──────┐ ┌──────┐ ┌──────┐                             │
│  │Wheat │ │Rice  │ │Cotton│  ← Crop Cards (max 6)       │
│  │Active│ │AtRisk│ │Active│                              │
│  └──────┘ └──────┘ └──────┘                             │
│                    [View all crops →]                     │
└─────────────────────────────────────────────────────────┘
```

**Interactive Elements:**
| Element | Behavior |
|---------|----------|
| Quick Actions dropdown | "+ New Crop", "Log Action", "Run Simulation" |
| Stat cards | Click → navigates to relevant page |
| Weather card | 5-day forecast with icons, expandable |
| Chart toggle | Pill tabs: Line / Bar / Pie — switches chart type |
| Map | Pannable, click marker → crop popup card |
| Crop cards | Click → `/crops/[id]`, hover lift |
| Alert banner | Dismiss button, click message → `/alerts` |
| View all link | → `/crops` |

---

### 4.4 Crops List

**Route:** `/crops`

**Layout:** Header + Filters + Grid/Table toggle + Crop cards/rows.

| Element | Type | Spec |
|---------|------|------|
| Page title | H1 | "My Crops" |
| New Crop button | Button (primary) | "+ New Crop" → `/crops/new` |
| View toggle | Segmented control | 🗃 Cards / 📋 Table |
| Filter: State | Dropdown | All / Created / Active / Delayed / AtRisk / Harvested |
| Filter: Crop Type | Dropdown | All / Wheat / Rice / Cotton / [dynamic] |
| Filter: Region | Dropdown | All / [user's regions] |
| Search | Search input | Search by crop name/variety |
| Sort | Dropdown | Newest / Oldest / Highest Risk / Highest Stress |
| Crop cards | Grid 3-col (desktop), 2-col (tablet), 1-col (mobile) | Frost card with: crop icon, type+variety, state badge, stress ring, sowing date, region |
| Crop table | Data table | Columns: Type, Variety, State, Day #, Stress, Risk, Region, Sowing Date |
| Pagination | Bottom bar | Page numbers + "Showing X of Y" |
| Empty state | Centered | Sprout icon + "No crops yet" + CTA |

---

### 4.5 Crop Detail

**Route:** `/crops/[id]`

**Layout:** Tabbed interface.

**Header:**
```
← Back    Wheat — HD-2967        [Active ●]        [⋮ More]
          Punjab, Ludhiana
```
| Element | Spec |
|---------|------|
| Back button | Ghost button, → `/crops` |
| Crop type + variety | H1 |
| Region | Subtitle |
| State badge | Colored pill |
| More menu | Dropdown: Edit, Change Sowing Date, Archive, Delete |

**Tabs:**

#### Tab 1: Overview
| Element | Spec |
|---------|------|
| Stat cards (4) | Day Number, Stress Score (progress ring), Risk Index (progress ring), Season |
| Growth Timeline | Horizontal stage indicator: Germination → Vegetative → Flowering → Maturity → Harvest |
| Weather Widget | Current + 3-day forecast for crop's region |
| Quick Actions | [Log Action] [Simulate] [Submit Yield] |

#### Tab 2: Actions
| Element | Spec |
|---------|------|
| Action history list | Chronological list, each with: date, type icon, category badge, notes |
| Log new action button | Floating action button → `/crops/[id]/log-action` |
| Filter by action type | Pill tabs: All / Irrigation / Fertilizer / Pesticide / Other |
| Empty state | "No actions logged yet" |

#### Tab 3: Analytics
| Element | Spec |
|---------|------|
| Stress score chart | Line chart with chart type toggle |
| Risk index chart | Line chart |
| Day-number progression | Line chart (baseline vs actual) |
| Deviation profile | Bar chart showing deviation per stage |
| Media gallery | Grid of uploaded photos with analysis status badges |

#### Tab 4: Simulate
| Element | Spec |
|---------|------|
| What-If form | Embedded from `/crops/[id]/simulate` |
| Simulation result | Side-by-side comparison card: Current vs Simulated |
| Reset button | Ghost button to clear simulation |

---

### 4.6 New Crop Form

**Route:** `/crops/new`

| Element | Type | Validation |
|---------|------|------------|
| Crop Type | Dropdown | Required |
| Variety | Text input | Optional |
| Sowing Date | Date picker | Required, ≤ today |
| Region | Dropdown (Indian states) | Required |
| Sub-Region | Text input | Optional |
| Land Area | Number input (acres) | Optional, > 0 |
| Rule Template | Dropdown (from API) | Optional |
| Create button | Primary | Loading state |
| Cancel | Ghost → back to `/crops` | — |

---

### 4.7 Log Action

**Route:** `/crops/[id]/log-action`

| Element | Type |
|---------|------|
| Crop info header | Mini crop card (type, state, day) |
| Action Type | Dropdown: Irrigation, Fertilizer, Pesticide, Harvest Prep, Soil Test, Other |
| Effective Date | Date picker, default today, must be ≥ sowing date |
| Category | Segmented: Timeline-Critical / Operational |
| Notes | Textarea |
| Idempotency Key | Auto-generated (hidden), shown as debug info |
| Submit | Primary button |
| Success toast | "Action logged successfully ✓" |

---

### 4.8 What-If Simulation

**Route:** `/crops/[id]/simulate`

| Element | Type |
|---------|------|
| Scenario builder | Form: "What if I apply [action] on [date]?" |
| Action type | Dropdown |
| Simulated date | Date picker |
| Run Simulation | Primary button, loading: "Simulating..." with pulse animation |
| Result comparison | Two frost cards side-by-side |
|   → Current | Shows current stress, risk, stage |
|   → Simulated | Shows projected stress, risk, stage with color diff highlights |
| State change animation | If state changes (Active → AtRisk), animate color shift |
| Disclaimer | Info banner: "Simulation only — no changes are saved to your crop" |

---

### 4.9 Yield Submission

**Route:** `/crops/[id]/yield`

| Element | Type |
|---------|------|
| Crop summary card | Mini card with crop info |
| Reported Yield | Number input (kg/acre) |
| Yield Unit | Dropdown: kg/acre, quintal/acre, ton/hectare |
| Harvest Date | Date picker |
| Confirmation modal | "Submit yield? This will finalize the crop lifecycle." → Confirm / Cancel |
| Result card | Shows: reported_yield, ml_yield_value, bio_cap_applied, verification_score |
| Success state | Crop card shows "Harvested" badge, confetti animation |

---

### 4.10 Service Marketplace

**Route:** `/services`

| Element | Spec |
|---------|------|
| Title | "Service Marketplace" |
| Search bar | Frosted, full-width |
| Filters card | Frosted card with: Region dropdown, Service Type dropdown, Crop Specialization dropdown |
| Provider cards grid | 3-col, each with: avatar, business name, region, trust score ring, service types (pill badges), verified badge, "Request Service" CTA |
| Trust score info | Collapsible info section at bottom explaining score formula |
| Empty state | "No providers found matching your criteria" |

---

### 4.11 Service Request

**Route:** `/services/request?provider=[id]`

| Element | Type |
|---------|------|
| Provider info card | Selected provider summary |
| Service type | Dropdown |
| Crop (link) | Dropdown from user's active crops |
| Preferred date | Date picker |
| Notes | Textarea |
| Submit request | Primary button |
| Success state | Toast + navigate to dashboard |

---

### 4.12 Service Review

**Route:** `/services/review`

| Element | Type |
|---------|------|
| Completed service info | Service card |
| Star rating | 5-star interactive (hover fill) |
| Review text | Textarea |
| Submit review | Primary |
| Validation | Cannot review if service not completed (eligibility check) |

---

### 4.13 Alerts Page

**Route:** `/alerts`

| Element | Spec |
|---------|------|
| Title + unread badge | "Alerts & Notifications" + red count pill |
| Filters card | Frost card: Alert Type dropdown, Severity dropdown, "Show acknowledged" toggle |
| Alert list | Stacked frost cards, each with: severity left border color, type icon, message, timestamp, [Acknowledge] button |
| Acknowledge action | Button → API call → toast "Alert acknowledged ✓" |
| Empty state | Bell icon + "All caught up!" |

---

### 4.14 Provider Dashboard

**Route:** `/provider`

Similar to Farmer Dashboard with different stats:

| Stat | Icon |
|------|------|
| Pending Requests | Inbox icon, yellow |
| Active Jobs | Hammer icon, blue |
| Completed | CheckCircle, green |
| Trust Score | Star, purple |

**Sections:**
1. Stat cards (4)
2. Incoming requests list — each with Accept button
3. Active jobs list — each with "Mark Complete" button

---

### 4.15 Provider Equipment

**Route:** `/provider/equipment`

| Element | Spec |
|---------|------|
| Equipment list | Data table or cards |
| Add Equipment | Modal form: name, type, rate, availability toggle |
| Edit/Delete | Inline actions per row |

---

### 4.16 Provider Reviews

**Route:** `/provider/reviews`

| Element | Spec |
|---------|------|
| Reviews list | Cards with: star rating, review text, farmer name, date |
| Average rating | Large stat card with star display |
| Filter | By rating (5/4/3/2/1 star pill buttons) |

---

### 4.17 Admin Panel

**Route:** `/admin`

| Element | Spec |
|---------|------|
| Stat cards (4) | Total Users, Active Crops, Providers, Active Requests — frost-tinted |
| Nav tiles (grid) | User Management, Provider Management — frost cards with icons, hover lift |

> **THEME MUST BE CONSISTENT** — admin uses same dark/light theme as rest of app. No white `bg-white` cards.

---

### 4.18 Admin: User Management

**Route:** `/admin/users`

| Element | Spec |
|---------|------|
| Data table | Sortable columns: Name, Email, Phone, Role, Region, Status, Created |
| Search | Filter by name/email |
| Actions per row | View, Suspend, Delete (danger) |
| Role badge | Colored pill per role |

---

### 4.19 Admin: Provider Management

**Route:** `/admin/providers`

| Element | Spec |
|---------|------|
| Data table | Business Name, Region, Trust Score, Verified status, Actions |
| Verify action | Button → confirmation modal |
| Suspend action | Danger button |
| Trust score column | Mini progress ring inline |

---

### 4.20 Admin: Rule Templates

**Route:** `/admin/templates`

| Element | Spec |
|---------|------|
| Template cards or table | Name, crop_type, version, status (draft → validated → active → deprecated) |
| Status workflow | Visual status stepper per template |
| Create new | → Modal form |
| Edit | → Inline editing or modal |
| Dual-admin approval | Approval status indicator, "Requires 2nd approval" badge |

---

### 4.21 Admin: System Health

**Route:** `/admin/health`

| Element | Spec |
|---------|------|
| Subsystem cards | ML, Weather, Media, Events — each with status dot (green/yellow/red) |
| Uptime chart | Line chart of health check trends |
| Last checked | Timestamp per subsystem |
| Refresh button | Manual health check trigger |

---

### 4.22 Admin: Dead Letters

**Route:** `/admin/dead-letters`

| Element | Spec |
|---------|------|
| DLQ table | Event type, entity, failure reason, retry count, created at |
| Retry action | Button per row → retry event processing |
| Purge action | Danger button → bulk delete |
| Filter | By event type, status |

---

### 4.23 Labor Page

**Route:** `/labor`

| Element | Spec |
|---------|------|
| Labor list | Cards or table with: name, type, rate, availability |
| Request labor | CTA button per worker |
| Filters | By type, availability |

---

## 5. Animation & Motion System

### 5.1 Animation Library

**Use:** Framer Motion (primary) + Tailwind CSS transitions (simple states).

### 5.2 Animation Catalog

| Animation | Trigger | Spec | Priority |
|-----------|---------|------|:--------:|
| **Skeleton shimmer** | Page/data loading | Gradient sweep 1.5s infinite | ⭐⭐⭐⭐⭐ |
| **Count-up numbers** | Stat cards mount | 0 → value, 800ms ease-out | ⭐⭐⭐⭐ |
| **Progress ring fill** | Stress/risk mount | Stroke-dashoffset animation 1s | ⭐⭐⭐⭐ |
| **Card hover lift** | Mouse hover | translateY(-2px), shadow increase, 200ms | ⭐⭐⭐ |
| **Page transition** | Route change | Fade + slide-up 200ms | ⭐⭐ |
| **Toast slide-in** | Notification | Slide from right 300ms | ⭐⭐⭐ |
| **State color shift** | Crop state change | Background color transition 500ms | ⭐⭐⭐⭐ |
| **Button press** | Click | Scale(0.97) 100ms | ⭐⭐ |
| **Processing pulse** | Async operations | Opacity pulse 1.5s | ⭐⭐⭐ |
| **Sidebar collapse** | Toggle | Width 300ms cubic-bezier | ⭐⭐ |
| **Modal backdrop** | Modal open/close | Opacity 0→1 200ms | ⭐⭐ |
| **Harvest confetti** | Yield submitted | Confetti particle burst 2s | ⭐ |

### 5.3 Transition Defaults

```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 200ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-spring: 500ms cubic-bezier(0.34, 1.56, 0.64, 1);
```

### 5.4 Rules

1. **Animation = system state feedback**, not decoration
2. Skeleton loaders for ANY async data (replay, ML, API calls)
3. Count-up for computed/probabilistic values (stress, risk, yield)
4. Color shift for crop state transitions
5. NO flashy/entertainment animations
6. Max total animation time on page load: **< 1 second**

---

## 6. Notification System

### 6.1 Four-Tier Architecture

| Tier | Component | Trigger | Duration | Position |
|------|-----------|---------|----------|----------|
| **Toast** | Floating card | Action feedback | Auto-dismiss 3s | Top-right, stackable |
| **Inline Banner** | In-page band | Persistent state | Stays until resolved | Top of relevant section |
| **Slide-in Panel** | Right drawer | Background events | Persistent, dismissable | Right edge, 320px wide |
| **Modal** | Centered overlay | Critical decisions | Until user acts | Center, backdrop blur |

### 6.2 Toast Specs

| Variant | Left Icon | Border Color |
|---------|-----------|-------------|
| Success | `CheckCircle` | `--color-success` |
| Error | `AlertCircle` | `--color-danger` |
| Warning | `AlertTriangle` | `--color-warning` |
| Info | `Info` | `--color-info` |
| Loading | `Loader2` (spinning) | `--color-primary` |

**Library:** `react-hot-toast` or `sonner`.

### 6.3 Modal Specs

- Backdrop: `rgba(0,0,0,0.5)` + `backdrop-filter: blur(4px)`
- Card: Frost card, max-width 480px
- Close: X button top-right + Escape key
- Actions: Right-aligned `[Cancel]` ghost + `[Confirm]` primary/danger

---

## 7. Accessibility & i18n

### 7.1 Accessibility (MSDD Section 7)

| Feature | Token | Spec |
|---------|-------|------|
| Large Text Mode (7.1) | `accessibility_settings.largeText` | Scale all font sizes by 1.5× |
| High Contrast Mode (7.2) | `accessibility_settings.highContrast` | Increase contrast ratios to WCAG AAA (7:1) |
| Pinned Sidebar | `accessibility_settings.sidebarPinned` | Sidebar stays expanded, never collapses |
| Reduced Motion | `accessibility_settings.reducedMotion` | Disable all animations except essential loaders |
| Theme Preference | `accessibility_settings.theme` | `"dark"` / `"light"` / `"system"` |

**Accessibility Panel:** Accessible from user avatar dropdown → "Accessibility Settings"

| Setting | Control |
|---------|---------|
| Theme | Segmented: Dark / Light / System |
| Large Text | Toggle |
| High Contrast | Toggle |
| Pin Sidebar | Toggle |
| Reduce Motion | Toggle |
| Language | Dropdown (see i18n) |

### 7.2 Internationalization (MSDD 7.6)

Design system must account for:

| Language | Direction | Font Support |
|----------|-----------|-------------|
| English | LTR | Inter |
| Hindi (हिन्दी) | LTR | Noto Sans Devanagari |
| Marathi (मराठी) | LTR | Noto Sans Devanagari |
| Punjabi (ਪੰਜਾਬੀ) | LTR | Noto Sans Gurmukhi |
| Tamil (தமிழ்) | LTR | Noto Sans Tamil |
| Telugu (తెలుగు) | LTR | Noto Sans Telugu |

**Implementation:** All user-facing strings wrapped in `t()` function (next-intl or i18next).
**Language stored in:** `user.preferred_language` field.

### 7.3 Keyboard Navigation

- All interactive elements focusable via Tab
- Visible focus ring: `2px solid var(--color-primary)`, `2px offset`
- Modal trap: Focus stays inside modal when open
- Sidebar: Arrow keys navigate items
- Escape: Close modals, dropdowns, slide-in panels

---

## 8. Responsive Breakpoints

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| `mobile` | < 640px | 1 column, bottom nav, no sidebar |
| `tablet` | 640–1024px | 2 columns, collapsible sidebar |
| `desktop` | 1024–1440px | 3 columns, sidebar expanded |
| `wide` | > 1440px | Max-width 1440px, centered |

### Per-Page Responsive Rules

| Page | Mobile | Tablet | Desktop |
|------|--------|--------|---------|
| Dashboard stats | 2×2 grid | 2×2 grid | 1×4 row |
| Crop cards | 1-col stack | 2-col grid | 3-col grid |
| Provider cards | 1-col stack | 2-col grid | 3-col grid |
| Data tables | Horizontal scroll | Full table | Full table |
| Chart+Map | Stacked vertical | Side-by-side | Side-by-side |
| Sidebar | Hidden (bottom nav) | Collapsed (64px) | Expanded (240px) |
| Filters | Collapsible accordion | Inline row | Inline row |

---

## Appendix: Route Map

| Route | Auth | Role | Page |
|-------|:----:|------|------|
| `/` | ❌ | any | Landing Page |
| `/login` | ❌ | any | Login |
| `/register` | ❌ | any | Register |
| `/dashboard` | ✅ | farmer | Farmer Dashboard |
| `/crops` | ✅ | farmer | Crops List |
| `/crops/new` | ✅ | farmer | New Crop Form |
| `/crops/[id]` | ✅ | farmer | Crop Detail (Tabbed) |
| `/crops/[id]/log-action` | ✅ | farmer | Log Action Form |
| `/crops/[id]/simulate` | ✅ | farmer | What-If Simulation |
| `/crops/[id]/yield` | ✅ | farmer | Yield Submission |
| `/services` | ✅ | farmer | Service Marketplace |
| `/services/request` | ✅ | farmer | Service Request Form |
| `/services/review` | ✅ | farmer | Service Review Form |
| `/alerts` | ✅ | farmer | Alerts & Notifications |
| `/labor` | ✅ | farmer | Labor Page |
| `/provider` | ✅ | provider | Provider Dashboard |
| `/provider/equipment` | ✅ | provider | Equipment Management |
| `/provider/reviews` | ✅ | provider | My Reviews |
| `/admin` | ✅ | admin | Admin Panel |
| `/admin/users` | ✅ | admin | User Management |
| `/admin/providers` | ✅ | admin | Provider Management |
| `/admin/templates` | ✅ | admin | Rule Templates |
| `/admin/health` | ✅ | admin | System Health |
| `/admin/dead-letters` | ✅ | admin | Dead Letter Queue |
