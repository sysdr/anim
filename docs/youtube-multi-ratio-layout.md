# YouTube multi-ratio layout (16:9, 9:16, 1:1)

Animations and text are laid out so the same design can be captured for **YouTube** in three aspect ratios:

| Ratio | Use case        | ViewBox (W×H) | Typical export |
|-------|------------------|---------------|----------------|
| **16:9** | Landscape, desktop | 960×540       | 1920×1080, 1280×720 |
| **9:16** | Shorts, mobile     | 540×960       | 1080×1920     |
| **1:1**  | Square, feed       | 540×540       | 1080×1080     |

## Safe zone (title-safe)

To keep **titles and key labels** readable in all three crops, they are constrained to a **safe zone** — the region that remains visible when the frame is center-cropped to each ratio.

- **16:9 (960×540):** center horizontal strip **x 328–632, y 0–540** (≈304×540 px).
- **9:16 (540×960):** center vertical strip **x 0–540, y 328–632** (540×304 px).
- **1:1 (540×540):** center square **x 118–422, y 118–422** (304×304 px).

General content keeps an **edge margin** of 50 px from the canvas edges; critical text is further restricted to the safe zone above.

## Implementation

- **ViewBox and safe zones:** `anim/web/services/gemini_service.py`  
  - `_VIEWBOX_BY_RATIO`: aspect ratio → (width, height).  
  - `_SAFE_ZONE_BY_RATIO`: aspect ratio → (x, y, width, height).  
  - `_safe_zone_description(aspect_ratio)` builds the string injected into the Architect prompts.

- **Prompts:** Both the cinematic SVG prompt and the Studio Architect prompt include:
  - Edge margin (50 px) for all content.
  - Explicit title-safe zone description so the model places titles and key labels inside it.

## Studio capture

1. Choose the target aspect ratio (16:9, 9:16, or 1:1) before generating.
2. Preview uses the same aspect ratio; the SVG viewBox matches it.
3. Use the preview’s resize handle or “Match capture size” to fit your recording area.
4. Record the preview (e.g. Chrome tab or selection); the visible region matches the chosen ratio so titles stay in frame.

## Export resolutions (reference)

| Ratio | Recommended resolution |
|-------|-------------------------|
| 16:9  | 1920×1080 (Full HD), 1280×720 |
| 9:16  | 1080×1920 (Shorts)     |
| 1:1   | 1080×1080               |
