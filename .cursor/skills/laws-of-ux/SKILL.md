---
name: laws-of-ux
description: >-
  Design interactive internal apps using Laws of UX (lawsofux.com).
  Use for intake forms, wizards, agent UIs, and admin panels with
  input, navigation, and state — not html-decks, slide HTML, or PPTX.
---

# Laws of UX — interactive apps only

Reference: **[Laws of UX](https://lawsofux.com/)** by Jon Yablonski.

**In scope:** **interactive** internal software — forms, wizards, agent panels, filters, tables with edit/save, steppers, modals, validation, loading states, and other UI driven by user input and application state.

**Out of scope:**

- **`html-decks/`** and all HTML deck / slide export work (any path under `**/html-decks/**`)
- HTML slide files, `slide_workspace_v0`, PPTX, static slide previews, `.page` slide rails
- Client-facing LoP slide content

Use McKinsey document standards and `write-html-slides` for deck work — not this skill.

---

## Pre-flight checklist

Before shipping or revising app/dashboard UI, verify:

1. **Fewer, clearer choices** — default path obvious; advanced options collapsed (Hick’s Law, Choice Overload).
2. **Chunked screens** — one primary goal per step; labels grouped (Chunking, Miller’s Law, Cognitive Load).
3. **Visual grouping** — related fields share region, spacing, or heading (Law of Proximity, Common Region, Similarity, Uniform Connectedness).
4. **Familiar patterns** — labels, buttons, and nav match common web/desktop conventions (Jakob’s Law, Mental Model).
5. **Large, reachable targets** — primary actions easy to hit; destructive actions separated (Fitts’s Law).
6. **Fast feedback** — loading, success, and errors within ~400ms perceived response where possible (Doherty Threshold).
7. **Progress visible** — steps, % complete, or “step 2 of 5” (Goal-Gradient Effect).
8. **One primary CTA** per view — secondary actions visually quieter (Von Restorff Effect).
9. **Forgiving inputs** — accept reasonable variants; validate with clear messages (Postel’s Law).
10. **No manual-first** — sensible defaults and inline hints, not a required readme (Paradox of the Active User).

When you change UI, name **2–4 laws** that drove the decision.

---

## Law → action (quick reference)

Definitions and research links: [lawsofux.com](https://lawsofux.com/).

### Perception and layout

| Law | Do this in apps/dashboards |
|-----|----------------------------|
| Aesthetic-Usability Effect | Clean spacing and consistent components increase trust; don’t sacrifice clarity for decoration. |
| Law of Proximity | Place related labels, inputs, and help text together. |
| Law of Common Region | Use cards, panels, or borders for one task or entity. |
| Law of Similarity | Same control types look and behave the same across the app. |
| Law of Uniform Connectedness | Use dividers, steppers, or lines to show flow between steps. |
| Law of Prägnanz | Prefer simple layouts; remove decorative clutter. |

### Decisions and complexity

| Law | Do this in apps/dashboards |
|-----|----------------------------|
| Hick’s Law | Reduce simultaneous choices; split long forms into steps. |
| Choice Overload | Limit filters, tabs, and menu items; offer “recommended” defaults. |
| Tesler’s Law | Move irreducible complexity to the right place (wizard vs settings), not away from the user entirely. |
| Occam’s Razor | Prefer the simplest flow that meets the requirement. |
| Pareto Principle | Optimize the 20% of screens/actions that carry 80% of usage. |
| Parkinson’s Law | Time-box optional fields; don’t expand forms to fill space. |

### Attention, memory, motivation

| Law | Do this in apps/dashboards |
|-----|----------------------------|
| Cognitive Load | Minimize simultaneous concepts; show only fields needed for this step. |
| Chunking | Group manifest rows, gates, or chapters into scannable sections. |
| Miller’s Law | Cap visible nav items and bullet lists (~5–9 chunks) per view. |
| Working Memory | Don’t require users to remember data from a prior step without showing it again. |
| Selective Attention | One focal headline and primary action per screen. |
| Serial Position Effect | Put critical warnings and primary CTAs at start or end of a step list. |
| Von Restorff Effect | One primary button style; don’t make every button “primary.” |
| Goal-Gradient Effect | Show progress toward completion (checklist, step indicator). |
| Zeigarnik Effect | Surface incomplete drafts or open items clearly. |
| Peak-End Rule | Make submit/success and error recovery polished. |
| Flow | Reduce interruptions during multi-step intake. |

### Interaction and systems

| Law | Do this in apps/dashboards |
|-----|----------------------------|
| Fitts’s Law | Large click/tap targets for primary actions; adequate spacing. |
| Jakob’s Law | Match platform patterns (tabs, modals, save, back). |
| Doherty Threshold | Skeleton loaders, optimistic UI, or instant validation feedback. |
| Postel’s Law | Lenient parsing of dates/paste; strict, helpful error messages on save. |
| Paradox of the Active User | Onboarding in-context; tooltips on first visit, not a PDF manual. |
| Mental Model | Use user’s words in nav (“Source manifest”, “Gate A”) not internal jargon. |
| Cognitive Bias | Avoid dark patterns; label AI-generated vs user-entered content. |

### Experience (use sparingly in B2B tools)

| Law | Do this in apps/dashboards |
|-----|----------------------------|
| Peak-End Rule | Confirm saves; clear recovery from errors. |
| Aesthetic-Usability Effect | Professional, calm visual system for long sessions. |

---

## Anti-patterns

- Ten equal-weight top-nav items with no default route.
- Long forms on one scroll with no step boundaries.
- No loading or save state (user double-submits).
- Breaking conventions (e.g. custom close icon behavior).
- Requiring documentation before first successful task.
- Applying slide-deck or **html-decks** rules to interactive app chrome.
- Using this skill on read-only or slide-preview HTML (not interactive).

---

## Deliverable note

After UI work, optionally add a short **UX rationale**: which laws you applied and what changed (e.g. “Split Step 3 into two steps — Hick’s Law + Cognitive Load”).
