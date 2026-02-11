# Inkcut Coordinate System Visual Diagrams

## 1. Coordinate System Visualization

### Qt Native System (Top-Down)
```
(0,0) ──────────────────────→ X
  │
  │
  │    Positive Y
  │    (downward)
  ↓
  Y
```

### Inkcut Preview System (Bottom-Up, after Y-flip)
```
  Y
  ↑
  │    Positive Y
  │    (upward)
  │
(0,0) ──────────────────────→ X
```

## 2. Origin Position Quadrants

The four supported origin positions map to four quadrants:

```
                    Material Area
         ┌─────────────────────────┐
         │                         │
    TL   │      Top-Left           │   TR
         │      (0, height)        │   (width, height)
         │                         │
         │        Design           │
         │      (may appear        │
         │       in any Q)         │
         │                         │
    BL   │      Bottom-Left        │   BR
         │      (0, 0)             │   (width, 0)
         └─────────────────────────┘

BL = Bottom-Left (default) - Origin at bottom-left
BR = Bottom-Right - Origin at bottom-right
TL = Top-Left - Origin at top-left
TR = Top-Right - Origin at top-right
```

## 3. Origin Position Transformations

### Bottom-Left (Default) - No Transformation
```
Design area:  [0, width] × [0, height]
Transform:    Identity (no change)
```

### Bottom-Right - Translate Left
```
Design area:  [-width, 0] × [0, height]
Transform:    translate(-width, 0)

Visual:
Before:               After:
┌─────────────┐      ┌─────────────┐
│  Design     │      │  Design     │
│  (0,0)      │  →   │  (-w,0)     │
└─────────────┘      └─────────────┘
                     ← width →
```

### Top-Left - Translate Down
```
Design area:  [0, width] × [-height, 0]
Transform:    translate(0, -height)

Visual:
Before:               After:
┌─────────────┐      ┌─────────────┐
│  Design     │      │  Design     │
│  (0,0)      │  →   │  (0,-h)     │
└─────────────┘      └─────────────┘
                     ↑ height ↓
```

### Top-Right - Translate Down-Left
```
Design area:  [-width, 0] × [-height, 0]
Transform:    translate(-width, -height)

Visual:
Before:               After:
┌─────────────┐      ┌─────────────┐
│  Design     │      │  Design     │
│  (0,0)      │  →   │  (-w,-h)    │
└─────────────┘      └─────────────┘
                     ← width → ↑ height ↓
```

## 4. Feed Direction Indicators

### Y-Axis Feed (Default)
```
Material feeds in Y direction (downward when origin is bottom-left)

Bottom-Left Origin:          Bottom-Right Origin:
┌──────────────────┐        ┌──────────────────┐
│ ← Material Feed  │        │  Material Feed → │
│      ↓           │        │      ↓           │
│    Design        │        │    Design        │
│      ↓           │        │      ↓           │
└──────────────────┘        └──────────────────┘

Top-Left Origin:             Top-Right Origin:
┌──────────────────┐        ┌──────────────────┐
│      ↑           │        │      ↑           │
│    Design        │        │    Design        │
│      ↑           │        │      ↑           │
│ ← Material Feed  │        │  Material Feed → │
└──────────────────┘        └──────────────────┘
```

### X-Axis Feed
```
Material feeds in X direction (rightward when origin is bottom-left)

Bottom-Left Origin:          Bottom-Right Origin:
┌──────────────────┐        ┌──────────────────┐
│ Design → Feed    │        │ Feed ← Design    │
│        Material  │        │ Material         │
└──────────────────┘        └──────────────────┘

Top-Left Origin:             Top-Right Origin:
┌──────────────────┐        ┌──────────────────┐
│ Design → Feed    │        │ Feed ← Design    │
│        Material  │        │ Material         │
└──────────────────┘        └──────────────────┘
```

## 5. Coordinate Transformation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  SVG Input from Inkscape                    │
│                (Top-left origin, Y down)                    │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Job.create() Processing                        │
│  • Copy positioning (with -y negation)                      │
│  • Scaling                                                  │
│  • Rotation (swap_xy)                                       │
│  • Alignment to material                                    │
│  Result: QPainterPath (bottom-left origin, Y up)            │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            Preview Display (Job Plugin)                     │
│  • Apply preview transform (Y-flip via QTransform)          │
│  • Apply device.transform() (scale, rotate)                 │
│  ✓ MISSING: Apply origin_position transform!                │
│  Result: Displayed in preview window                        │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            Device.init() Processing                         │
│  • Applies swap_xy, scale (with mirror)                     │
│  • Applies feed_to_end translation                          │
│  Result: QPainterPath in device coordinates                 │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            Device.transform() Final Transforms              │
│  • Applies scale                                            │
│  • Applies rotation                                         │
│  Result: QPainterPath ready for device protocol             │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│         Device Protocol Handler (HPGL, CAMM-GL, etc)        │
│              Sends to physical device                       │
└─────────────────────────────────────────────────────────────┘
```

## 6. Y-Coordinate Negation Points

These are the key locations where `-y` is applied:

```
1. Preview Updates (preview/plugin.py):
   self.paths[0].lineTo(x, -y)

   Reason: Convert device position (top-down) to preview (bottom-up)

2. Job Processing (job/models.py):
   QTransform.fromTranslate(x, -y).map(path)

   Reason: Position copies in preview coordinate system

3. Device Init (device/plugin.py):
   model.translate(x, -y)

   Reason: Position design relative to device origin

All three serve the same purpose: Convert between coordinate systems
```

## 7. Current vs. Desired Flow (Origin Position)

### Current Flow (Missing Origin Transform in Main Preview)
```
Job Preview                          Live Preview
    ↓                                    ↓
Design at (0,0)              Design at origin_position
(bottom-left only)           (correct position) ✓
❌ MISMATCH
```

### Desired Flow (With Origin Transform in Main Preview)
```
Job Preview                          Live Preview
    ↓                                    ↓
Design at origin_position    Design at origin_position
(correct position) ✓          (correct position) ✓
✓ CONSISTENT
```

## 8. Device Configuration Impact on Coordinates

```
Configuration Option    Impact on Coordinates
─────────────────────   ─────────────────────
origin_position         Translates entire design
feed_axis              Controls feed direction indicator
swap_xy                Rotates 90° (+ scales to -1, 1)
mirror_x               Scales X by -1
mirror_y               Scales Y by -1
scale[0], scale[1]     Scales X and Y independently
rotation               Rotates final output

Order of Application (in Device.init()):
1. swap_xy (if enabled)
2. scale (with mirror applied)
3. feed_to_end (if enabled)
```

## 9. Summa D760 Configuration Example

For a Summa D760 with:
- Origin at bottom-right
- Y-axis feed (default)
- No swap_xy needed

```
Configuration:
  origin_position: 'bottom_right'
  feed_axis: 'y'
  swap_xy: False
  mirror_x: False
  mirror_y: False

Transformation:
  1. Job creates design at (0, 0) [bottom-left]
  2. Origin transform translates to (-width, 0) [bottom-right]
  3. Design is now positioned correctly for Summa D760

Result in Preview:
  ┌──────────────────┐
  │ Origin (dot) →   │
  │                  │
  │       Design     │
  │       (cut)      │
  │                  │
  │       (move)     │
  └──────────────────┘
```

## 10. Coordinate System Decision Matrix

| Use Case | Coordinate System | Pros | Cons |
|----------|-------------------|------|------|
| Preview/UI Display | Cartesian-like (bottom-left, Y↑) | Intuitive, matches expectations | Requires Y-flips for Qt |
| Device Output | Device-specific | Matches hardware | Complex transformations |
| Internal Processing | Hybrid (context-dependent) | Flexible | Hard to track |

**Recommendation**: Continue using Cartesian-like system for preview/UI, but make coordinate transformations explicit and centralized.
