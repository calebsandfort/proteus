# Unit 9: Chat UI Components

> **Status:** Implemented
> **FR Coverage:** FR-1.1, FR-1.3, FR-1.4, FR-1.5, FR-1.6, FR-1.7, FR-1.8
> **Dependencies:** IU-3 (Data API), IU-8 (Response Generation & Streaming)*

## Overview

Unit 9 implements the frontend chat interface for Proteus, providing the conversational interaction layer that connects users to the AI-powered analytics pipeline. This unit uses **CopilotKit** as the primary framework, integrated with a custom component architecture that delivers a professional-grade chat experience with observability, feedback states, and error handling.

The chat UI is positioned as a right-aligned sidebar (380-420px width) in the desktop viewport, with responsive behavior that collapses into a drawer below 1024px. The implementation handles the complete user interaction lifecycle: from query input through multi-turn conversation management, pipeline stage tracking, loading feedback, error recovery, and finally visualization rendering in the main canvas area.

The unit directly interfaces with IU-8 (Response Generation) via the `/api/copilotkit` endpoint, consuming SSE streaming events and rendering them as chat messages with embedded visualizations. The 4-level observability system allows analysts to inspect the AI pipeline internals without overwhelming casual users.

## Functionality Implemented

- **Layout and Structure** (FR-1.1) — Right-aligned 380-420px ChatSidebar with mobile drawer collapse below 1024px, visualization canvas in main area, session history persistence
- **Multi-Turn Conversation** (FR-1.2*) — Handled by useConversation hook with multi-tool pending/completed tracking, though core multi-turn logic lives in IU-8
- **Observability Panel** (FR-1.3) — Toggle control with localStorage persistence, expand icons on chat messages, inline JSON viewer
- **Observability Progressive Disclosure** (FR-1.4) — 4-level system: clean (L0), toggle active (L1), expanded JSON (L2), raw API response (L3)
- **Model Selector** (FR-1.5) — Dropdown in header area for response generation model selection, integrates with CopilotKit provider
- **Loading and Feedback States** (FR-1.6) — Stage indicator (5 stages), skeleton loaders with shimmer animation, per-tool pending indicators, inline result rendering
- **Error Handling and HITL Clarification** (FR-1.7) — Inline clarification cards (max 3 options), error messages with suggestions, rate limit countdown, session timeout banner
- **Empty State** (FR-1.8) — Centered placeholder with sample queries, animated visualization placeholder, immediate input availability

## Implementation Details

### Technology Stack

- **Framework:** Next.js 14 with App Router
- **Chat SDK:** CopilotKit `@copilotkit/react-core` and `@copilotkit/runtime`
- **UI Components:** ShadCN/ui primitives with Tailwind CSS
- **State Management:** React hooks (useState, useEffect) with localStorage persistence
- **Testing:** Vitest with React Testing Library

### Architecture Patterns

**Component Composition:**
The chat interface follows a layered architecture:
1. **CopilotChat** — Root wrapper integrating CopilotKit provider with custom components
2. **ChatSidebar** — Container with responsive collapse logic
3. **Message Components** — MessageBubble, ClarificationCard, EmptyState
4. **Feedback Components** — StageIndicator, ChartSkeleton, ErrorMessage
5. **Hooks** — useObservability, useSidebar, useConversation

**Responsive Behavior:**
The useSidebar hook manages a 1024px breakpoint. Above this threshold, the chat appears as a fixed-width sidebar. Below it, the sidebar collapses into a drawer triggered by a FloatingActionButton component.

**Observability System:**
The 4-level progressive disclosure uses localStorage for persistence:
- Level 0: Hidden (default)
- Level 1: Toggle ON shows expand icons and pipeline metadata
- Level 2: Expanded JSON viewer with syntax highlighting and collapsible nodes
- Level 3: Raw API request/response dump

### Key Design Decisions

1. **Inline Clarification over Modals** — HITL clarification appears as inline cards within the chat stream, keeping the user in the conversational flow
2. **Per-Tool Loading Indicators** — Multi-tool queries display individual "Waiting for results..." per pending tool rather than a monolithic spinner
3. **Skeleton Over Spinner** — Chart-shaped skeleton loaders provide visual continuity during rendering
4. **localStorage for Observability** — Panel state persists across sessions via localStorage key `proteus_observability_enabled`
5. **Session Timeout Banner** — Not a modal; inline banner preserves conversation context for 30 minutes

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/components/chat/copilot-chat.tsx` | Main CopilotKit wrapper integrating provider with custom chat components |
| `frontend/src/components/chat/ChatSidebar.tsx` | Desktop sidebar container (380-420px width) |
| `frontend/src/components/chat/ChatDrawer.tsx` | Mobile drawer with FAB trigger |
| `frontend/src/components/chat/MessageBubble.tsx` | Chat message component with 4-level observability expand |
| `frontend/src/components/chat/ClarificationCard.tsx` | Inline HITL clarification card (max 3 options) |
| `frontend/src/components/chat/EmptyState.tsx` | Centered placeholder with sample queries |
| `frontend/src/components/chat/FloatingActionButton.tsx` | Mobile FAB trigger for drawer |
| `frontend/src/components/feedback/StageIndicator.tsx` | 5-stage pipeline display (Parsing, Retrieving, Extracting, Querying, Generating) |
| `frontend/src/components/feedback/ChartSkeleton.tsx` | Shimmer skeleton loader with chart shapes |
| `frontend/src/components/feedback/ErrorMessage.tsx` | Error display with rate limit countdown and retry |
| `frontend/src/hooks/use-observability.ts` | 4-level progressive disclosure with localStorage persistence |
| `frontend/src/hooks/use-sidebar.ts` | Mobile breakpoint handling with auto-collapse |
| `frontend/src/hooks/use-conversation.ts` | Multi-turn conversation state, tool tracking, loading level calculation |
| `frontend/src/app/chat/page.tsx` | Chat page route |

## Integration Points

### This Unit Provides

- **To IU-10 (Visualization Engine):** MessageBubble renders visualization data from tool results; receives ChartType, KPI data, or table data
- **To IU-11 (Model Selector):** ModelSelector integrates into ChatSidebar header; selected model passed to CopilotKit provider
- **To Backend:** SSE consumer at `/api/copilotkit` endpoint; sends messages, receives streaming responses
- **To localStorage:** Observability toggle state persistence

### This Unit Depends On

- **IU-8 (Response Generation):** `/api/copilotkit` endpoint for SSE streaming
- **IU-3 (Data API):** Query results embedded in tool messages for visualization
- **CopilotKit Runtime:** `@copilotkit/runtime` for agent integration
- **Next.js Environment:** App Router structure for page and API routes

## Usage Guide

### Running the Chat Interface

The chat UI is available at `/chat` route:
```bash
cd frontend
pnpm dev
# Navigate to http://localhost:3000/chat
```

### CopilotKit Endpoint

The frontend proxies to the backend CopilotKit endpoint:
```typescript
// frontend/src/app/api/copilotkit/route.ts
// POST /api/copilotkit -> forwards to backend FastAPI
```

Backend endpoint (IU-8):
```python
# backend/src/api/router.py
@router.post("/api/copilotkit")
async def copilotkit_endpoint(request: Request):
    # SSE streaming response
```

### Observability Toggle

Enable via localStorage or toggle UI:
```typescript
// localStorage key
'proteus_observability_enabled' // 'true' | 'false'
```

### Mobile Breakpoint

Sidebar collapses below 1024px:
```typescript
const isMobile = useMediaQuery('(max-width: 1023px)');
```

### Testing

Run component tests:
```bash
cd frontend
pnpm test -- --run components/chat/
pnpm test -- --run components/feedback/
pnpm test -- --run hooks/
```

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `08213ad` | 2026-04-04 | feat: implement Unit 9 Chat UI Components |
| `987c8b0` | 2026-04-04 | test: add Unit 9-10 contract tests |
| `823a153` | 2026-03-26 | fix: update dependencies and resolve copilotkit/langgraph conflict |

---

*Note: FR-1.2 (Multi-Turn Conversation) core logic is implemented in IU-8 (Response Generation & Streaming) with frontend support via useConversation hook. The implementation plan notes IU-3 and IU-8 as soft dependencies (*), allowing parallel development.*