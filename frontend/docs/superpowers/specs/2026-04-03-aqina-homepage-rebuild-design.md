# Aqina Homepage Rebuild Design

Date: 2026-04-03
Project: `/Users/ginooh/Documents/Aqina 滴鸡精/aqina-chicken-essence/frontend`
Reference: `/Users/ginooh/Documents/Aqina 滴鸡精/stitch_premium_conversion_hybrid_prd (1)/code.html`
Reference image: `/Users/ginooh/Documents/Aqina 滴鸡精/stitch_premium_conversion_hybrid_prd (1)/screen.png`

## Goal

Rebuild the homepage presentation layer so the live Aqina site matches the provided premium conversion reference as closely as possible, while preserving the current data and checkout behavior.

The redesign is a homepage-only UI refactor. It must feel like the reference screenshot and reference HTML:

- mobile-first
- dark green luxury palette
- gold framing and typography accents
- strong vertical sales narrative
- simplified fixed header
- premium pricing cards
- preserved shopping and checkout flows

## Core Constraints

These behaviors must remain intact:

- locale-based routing in `src/app/[locale]/`
- translation loading from `messages/en.json` and `messages/zh.json`
- product loading via `getProducts()` in `src/lib/product-service.ts`
- add-to-cart behavior via `useCartStore`
- checkout modal submit flow via `createOrder`
- persistent cart drawer behavior in `Header`
- global WhatsApp floating button

These behaviors will change:

- homepage visual system
- homepage section order
- homepage component composition
- homepage copy structure to better match the reference layout

These behaviors will not change:

- Firestore schema
- product shape returned by `getProducts()`
- `DisplayProduct` contract
- cart store contract
- checkout modal props contract
- order creation payload shape

## Visual Direction

Adopt the reference aesthetic directly.

### Palette

- page background: `#091A14`
- elevated surfaces: `#112B22`
- primary gold: `#D4AF37`
- bright CTA yellow: `#FFB800`
- body text: warm off-white with muted green-gray secondary text
- borders: low-contrast gold and deep green outlines

### Typography

- headings: `Cormorant Garamond`
- body and UI: `Plus Jakarta Sans`
- Material Symbols Outlined used where the reference relies on category/cart icons

### Composition

- dense vertical stacking on mobile
- strong image-first rhythm
- large hero with text over image
- alternating image and copy modules
- thin borders and premium card framing
- less rounded than current site, closer to the reference

## Homepage Information Architecture

The homepage will render in this order:

1. Fixed Header
2. Identity Selector
3. Hero Section
4. Target Audience Section
5. Science / Trust Section
6. Product Pricing Section
7. Mobile Floating CTA
8. Footer

The following current homepage sections will be removed from the page flow:

- `StorySection`
- `PolicySection`
- `TestimonialsSection`
- `FAQSection`

## Component Plan

### 1. Header

Replace the current lifestyle header with a fixed premium header matching the reference:

- compact height
- dark translucent background
- blur effect
- left-aligned Aqina logo/wordmark
- right-aligned cart trigger only
- no desktop nav
- no visible language toggle
- keep existing cart drawer wiring and cart count behavior

Implementation note:

- keep `CartDrawer`
- keep `useCartStore`
- preserve `initializeCart()` behavior on mount
- remove menu drawer and locale switch UI from homepage header experience

### 2. Identity Selector

Add a new horizontally scrollable selector bar directly below the header.

Items:

- Workplace
- Maternity
- Halal
- Recovery

Behavior:

- anchor links to matching content blocks
- mobile-first horizontal overflow
- premium pill buttons with icon + label
- translated labels from messages

This is a presentation aid only. It must not affect data fetching.

### 3. Hero Section

Rebuild hero to match the reference:

- around `85vh` height on mobile/desktop with sensible min height
- full-bleed background image
- dark top-to-bottom overlay gradient
- gold-emphasis headline
- supporting text below
- primary yellow CTA linking to pricing section

Hero copy remains localized through `messages`.

The hero must feel cinematic and conversion-focused, not airy or editorial like the current version.

### 4. Target Audience Section

Replace `ProblemSolutionSection` with a new `TargetAudienceSection`.

Four audience blocks:

- Workplace
- Maternity
- Recovery
- Halal

Layout characteristics based on reference:

- alternating image/content rhythm
- nested image grids in some blocks
- compact eyebrow labels with icons
- gold-accent headings
- muted premium paragraph styling
- section background alternates between page background and elevated surface

Content source:

- use localized copy from new translation keys
- do not fetch new backend data

### 5. Science / Trust Section

Retain the trust/certification concept but restyle it to match the reference.

Visual characteristics:

- dark premium layout
- one primary feature card on the left
- certification imagery / trust tiles on the right
- concise copy
- gold section heading

This remains presentation-only and should not introduce new APIs.

### 6. Product Pricing Section

Rebuild the pricing grid so it visually matches the reference while keeping the current product logic.

Requirements:

- 4 product cards
- recommended product visually emphasized
- gold borders, labels, and pricing accents
- card layout supports current `DisplayProduct` fields:
  - `name`
  - `price`
  - `image`
  - `label`
  - `popular`
  - `badge`
- keep `onAddToCart(product)`
- keep `onBuyNow(product)`
- keep loading skeleton behavior

Structural note:

- the section may use a redesigned `ProductCard`
- product source remains the current `page.tsx` state fed by `getProducts()`

### 7. Mobile Floating CTA

Add a dedicated mobile-only sticky bottom CTA similar to the reference.

Behavior:

- visible only on small screens
- anchored above safe-area bottom
- links to the pricing section or triggers purchase intent
- does not replace the global WhatsApp floating button

The WhatsApp button remains globally available and should be visually adjusted only if needed to avoid overlap.

### 8. Footer

Simplify the footer to match the reference.

Requirements:

- logo / brand lockup
- small navigation
- copyright row
- reduced visual noise

## i18n Plan

The homepage must continue supporting current locale routing.

Changes required:

- add new translation keys for:
  - identity selector labels
  - target audience section
  - science section wording if current copy no longer fits
  - footer/nav wording if simplified
  - mobile floating CTA
- keep both `messages/en.json` and `messages/zh.json` in sync

The language toggle will be hidden in the homepage header UI, but locale-specific rendering still happens via the existing route segment and messages.

## Data and API Safety Plan

To avoid regressions during the refactor:

- `src/app/[locale]/page.tsx` remains the owner of product fetch state
- `getProducts()` remains unchanged
- fallback hardcoded products remain as safety net unless a later cleanup is explicitly requested
- `handleAddToCart` remains a thin pass-through to `useCartStore`
- `handleBuyNow` remains the trigger for `CheckoutModal`
- `CheckoutModal` submit logic remains untouched unless styling-only changes are required later

No new backend calls are allowed in this redesign.

## File-Level Change Plan

Expected file changes:

- `src/app/[locale]/layout.tsx`
- `src/app/[locale]/page.tsx`
- `src/app/globals.css`
- `src/components/Header.tsx`
- `src/components/HeroSection.tsx`
- `src/components/ProductPricingSection.tsx`
- `src/components/ProductCard.tsx`
- `src/components/Footer.tsx`
- `src/components/ScienceEndorsementSection.tsx`
- `src/components/WhatsAppButton.tsx` if overlap adjustments are needed
- new `src/components/IdentitySelector.tsx`
- new `src/components/TargetAudienceSection.tsx`
- new `src/components/MobileFloatingCTA.tsx`
- `messages/en.json`
- `messages/zh.json`

Expected removals from homepage usage:

- `StorySection`
- `PolicySection`
- `ProblemSolutionSection`
- `TestimonialsSection`
- `FAQSection`

These components may remain in the codebase initially if removal is not needed for the refactor itself.

## Validation Plan

Before calling the redesign complete:

- run lint
- run production build if feasible
- verify homepage renders in both locales
- verify cart drawer opens from header
- verify add-to-cart still works from pricing cards
- verify buy-now still opens checkout modal
- verify checkout modal still submits through existing order flow
- verify mobile floating CTA does not obstruct WhatsApp button

## Risks

### Risk: UI refactor accidentally changes shopping flow

Mitigation:

- preserve `page.tsx` ownership of commerce handlers
- treat section rebuild as presentation-only
- avoid refactoring checkout logic during homepage redesign

### Risk: reference design conflicts with existing localized copy lengths

Mitigation:

- design for multi-line heading and paragraph wrapping
- keep buttons and pills resilient to longer Chinese copy

### Risk: floating CTA collides with WhatsApp button

Mitigation:

- reserve separate vertical positions on mobile
- keep WhatsApp as a side floating action and CTA as bottom full-width action

## Decision

Proceed with a homepage presentation-layer rebuild, not a partial reskin and not a direct HTML transplant.
