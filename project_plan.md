# Navis  
### Don’t just browse. Arrive.

---

## Problem Statement  
The web is built around pages, menus, and navigation trees, while users think in goals.  
This gap makes navigating large websites difficult—especially for non-technical users, elderly people, and physically handicapped users—turning simple tasks into complex, error-prone journeys.

Existing tools focus on reading or searching content, not **navigating toward outcomes**.

---

## Solution Overview  
**Navis** is a **voice-driven AI navigation agent** implemented as a Chrome extension.  
Users express goals in natural language, and Navis guides them through the current website by understanding intent, inspecting page structure, and navigating step-by-step toward the destination.

> **Don’t just browse. Arrive.**

---

## Who Benefits & Why It Matters  
- **Non-technical and elderly users:** reduced dependency on memorizing UI paths  
- **Physically handicapped users:** hands-free interaction with the web  
- **All users:** lower cognitive load and faster task completion  

Navis improves **accessibility** and **productivity** by shifting interaction from manual browsing to intent-based navigation.

---

## Ideation & Differentiation  
- Focuses on **goal-based navigation**, not command execution  
- Embedded directly into the browsing flow (not a side chatbot)  
- Treats websites as navigable environments, not static documents  
- Designed around human-AI collaboration, not full autonomy  

Navis bridges how humans *think* with how websites are *structured*.

---

## Technical Approach (High Level)

### Architecture Choice  
Navis is built as a **Chrome extension** to operate within real browser security constraints while remaining deployable today.

### Core Technical Components  
- **Voice Input:** Speech-to-text for natural goal expression  
- **Intent Understanding:** LLM interprets user goals at a semantic level  
- **Page Inspection:** DOM and Accessibility Tree analysis  
- **Interactive Element Detection:**  
  Inspired by WebNav, Navis identifies actionable elements using:
  - Semantic roles (links, buttons, inputs)
  - ARIA labels
  - Headings and structural landmarks
  - Visibility and interactivity heuristics
- **Dynamic Navigation Planning:**  
  Task-specific, ephemeral agent graphs are created per user goal to plan and execute navigation steps.
- **Guided Execution:**  
  Scroll, highlight, and navigate with explicit user confirmation for actions.

---

## Human-in-the-Loop Design  
Navis intentionally pauses for:
- Authentication and login
- CAPTCHA or “prove you are human” steps
- Sensitive actions (downloads, submissions)

This ensures safety, trust, and transparency while keeping the user in control.

---

## Constraints & Scope Control  
To prevent overreach and ensure feasibility, Navis is intentionally constrained:

- Operates only within the **current browser tab and domain**
- No infinite web crawling or cross-site automation
- No access to stored passwords or credential bypass
- No autonomous form submission
- No invisible background actions
- Session-scoped site understanding (no permanent scraping)

These constraints are **design decisions**, not limitations.

---

## Feasibility  
All core features—voice input, DOM inspection, navigation, highlighting, and downloads—are supported by existing browser extension APIs, making Navis practical and implementable within a hackathon timeframe.

---

## Business & Deployment Feasibility  
Navis can be adopted as:
- An accessibility enhancement for organizations
- A productivity tool for complex portals
- A white-label navigation layer for institutions

The primary value is delivered to organizations responsible for digital experiences rather than individual end users.

---

## Path Beyond the Demo  
The Chrome extension serves as a validation layer for agentic, voice-based web navigation.

Future directions include:
- Persistent cross-session navigation memory
- Domain-optimized agents with permission
- Multilingual and low-bandwidth support
- Deeper browser-level integration

---

## Conclusion  
Navis introduces a new interaction model for the web—one centered on **intent, guidance, and arrival**, rather than pages and menus.

> **Don’t just browse. Arrive.**
