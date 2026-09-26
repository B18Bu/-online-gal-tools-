---
name: 地球online gal工具包
description: 深色 Windows 私聊回复辅助窗口
colors:
  canvas: "#0d1216"
  surface: "#151d22"
  surface-raised: "#202a30"
  surface-active: "#2a373d"
  text: "#eef7f5"
  muted: "#a6b8b5"
  accent: "#45d7c1"
  accent-deep: "#2ba994"
  warning: "#f0bf72"
  error: "#f18377"
typography:
  display:
    fontFamily: "Microsoft YaHei UI, sans-serif"
    fontSize: "16px"
    fontWeight: 700
  title:
    fontFamily: "Microsoft YaHei UI, sans-serif"
    fontSize: "11px"
    fontWeight: 700
  body:
    fontFamily: "Microsoft YaHei UI, sans-serif"
    fontSize: "10px"
    fontWeight: 400
  label-mono:
    fontFamily: "Cascadia Mono, monospace"
    fontSize: "9px"
    fontWeight: 400
spacing:
  tight: "5px"
  control: "8px"
  group: "14px"
  frame: "22px"
components:
  button-primary:
    backgroundColor: "{colors.accent-deep}"
    textColor: "{colors.canvas}"
    rounded: "0px"
    padding: "9px"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "0px"
    padding: "9px"
  reply-choice:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "0px"
    padding: "8px"
---

# Design System: 地球online gal工具包

## Overview

**Creative North Star: "The Quiet Reply Desk"**

This is a compact, no-terminal operating surface for a private desktop workflow. Graphite layers hold the work in a low-light chat setting while sea-glass actions distinguish the few moments that need a decision: select a tone, generate, then copy a reply.

The interface favors visible state over decoration. The latest incoming text is given a stable reading area; candidate replies are direct controls rather than ornamental cards; errors and progress occupy the same small status channel so the tool stays compact.

**Key Characteristics:**

- Restrained dark tonal layering rather than floating-card depth.
- One sea-glass action color, with warm warning and error exceptions.
- Dense, desktop-native controls with explicit enabled, disabled, and selected states.

## Colors

The system is restrained: graphite surfaces establish hierarchy, sea-glass marks active intent, and warm signals are reserved for recovery states.

### Primary

- **Sea-glass action:** Used for primary generation actions, the selected relationship segment, focus, and ready status.

### Secondary

- **Warm warning:** Reserved for missing configuration or a deliberate no-reply recommendation.
- **Warm error:** Reserved for recoverable OCR, API, and copy failures.

### Neutral

- **Night canvas:** Holds the application shell.
- **Tonal work surfaces:** Separate read-only message content, controls, and active hover states without shadows.
- **Bright text and muted metadata:** Keep the operational reading order clear in low light.

**The One Action Color Rule.** Sea-glass is for a selected state or an action that advances the workflow, never for decorative emphasis.

## Typography

**Display Font:** Microsoft YaHei UI

**Body Font:** Microsoft YaHei UI

**Label/Mono Font:** Cascadia Mono

**Character:** Bold Chinese UI type carries product and task headings; the mono face is restricted to shortcut and key-entry metadata.

### Hierarchy

- **Display:** Used only for the two-line product title.
- **Title:** Used for message, relationship, and candidate sections.
- **Body:** Used for chat text, relationship labels, actions, candidates, and status.
- **Label:** Used for the shortcut footer and API key entry.

**The Read-Then-Act Rule.** The incoming message remains the first large body region; controls follow it in task order.

## Layout

The fixed desktop panel uses a single vertical column with a 22px outer frame and 14px separation between task groups. Header status, the message readout, relationship segments, primary controls, and reply choices form a top-to-bottom sequence. Candidate rows have fixed rhythm and do not change width when content changes.

The panel is compact enough for a chat-side workflow and has a user-controlled topmost state. High-DPI layouts use reduced vertical padding to keep all three reply choices reachable.

## Elevation & Depth

Depth is tonal, not shadow-based. The canvas, inset message surface, raised secondary controls, and active surfaces each have distinct dark values. Windows chrome provides the only external elevation; in-panel controls remain flat.

**The Tonal Layer Rule.** Use a surface change to communicate hierarchy or interaction state. Do not add decorative glow, gradients, or floating shadows.

## Shapes

Controls and content regions use square, native Tkinter forms with no ornamental rounding. The status dot and application icon are the only circular geometry. This keeps the interface compact and intentionally desktop-native.

## Components

### Buttons

- **Primary:** Sea-glass background for “生成回复”; disabled while uncalibrated or generating.
- **Secondary:** Raised graphite background for “校准区域” and dialog cancellation.
- **Reply choice:** Full-width graphite rows that become enabled only for the current generation and state “点击复制” in their label.

### Segmented Relationship Control

- **Style:** Five equal-width controls in one row.
- **State:** The selected relation receives the primary action color; changing relation invalidates prior candidate replies.

### Readout Surface

- **Style:** Inset dark panel with bright body text.
- **Purpose:** Shows the latest incoming message without making it clickable or editable.

### API Key Field

- **Style:** Near-black entry field with a sea-glass focus outline.
- **State:** Uses masked input and keeps the value only in runtime memory.

## Do's and Don'ts

### Do:

- **Do** use the primary action color only for the selected relationship and the next task action.
- **Do** reset reply choices whenever their relationship or generation context is no longer current.
- **Do** keep chat text and candidate actions visually distinct through hierarchy and labeling.
- **Do** keep manual copy and manual message sending as separate user-controlled steps.

### Don't:

- **Don't** turn the panel into a terminal transcript or a dashboard.
- **Don't** add gradients, glass effects, decorative shadows, or extra color accents.
- **Don't** leave stale candidates enabled while a new generation is pending.
- **Don't** make screenshots or API keys persistent by default.
