# Inkcut Coordinate System - Executive Summary

## Quick Answer to Your Question

**Q: Does Inkcut use a Cartesian coordinate system?**

**A: Partially, but with important caveats.**

The **preview/UI layer** uses a Cartesian-like system (bottom-left origin, Y increases upward), but this is achieved through Y-flip transformations applied to Qt's native top-down coordinate system. The **device output layer** uses device-specific transformations that can completely change the coordinate system based on `swap_xy`, `mirror_x`, `mirror_y`, and other settings.

---

## What You Need to Know

### 1. The Coordinate System is Layered

```
Layer 1 (Qt Native)        →  Top-left origin, Y down
                ↓ (Y-flip)
Layer 2 (Preview/UI)       →  Bottom-left origin, Y up (Cartesian-like)
                ↓ (device transform)
Layer 3 (Device Output)    →  Device-specific (configurable)
```

### 2. Y-Coordinate is Negated Multiple Times

Throughout the codebase, you'll see `-y` applied at several points:
- Preview updates: `self.paths[0].lineTo(x, -y)`
- Job processing: `QTransform.fromTranslate(x, -y)`
- Device init: `model.translate(x, -y)`

This is **normal and correct** - it's converting between coordinate systems.

### 3. The Design Doesn't Shift in Main Preview (The Issue)

**Current Behavior**:
- Live preview: Design shifts to correct origin position ✓
- Main preview: Design stays at bottom-left ✗

**Root Cause**: `inkcut/job/plugin.py` doesn't apply origin position transformation in `_refresh_preview()`, while `inkcut/device/plugin.py` does apply it in `_reset_preview()`.

**Solution**: Apply the same origin transformation in both places.

---

## Where All the Transforms Are

### Preview Layer (`inkcut/preview/plugin.py`)
```python
def _default_transform(self):
    return QtGui.QTransform.fromScale(1, -1)  # Y-flip
```
- Converts Qt's top-down to bottom-up
- Applied to all preview items

### Job Processing (`inkcut/job/models.py`)
```python
model.addPath(QTransform.fromTranslate(x, -y).map(path))  # Y negation
```
- Positions copies in preview coordinate system
- Also applies scaling and rotation

### Device Output (`inkcut/device/plugin.py`)
```python
def transform(self, path):
    t = QtGui.QTransform()
    if config.scale:
        t.scale(*config.scale)
    if config.rotation:
        t.rotate(config.rotation)
    return t.map(path)
```
- Applies final device-specific transforms
- Called by both preview and actual device output

### Device Initialization (`inkcut/device/plugin.py`)
```python
model = job.create(swap_xy=config.swap_xy, scale=scale)
if job.feed_to_end:
    x, y, z = self.origin
    model.translate(x, -y)  # Y negation
```
- Applies swap_xy (90° rotation)
- Applies mirror_x and mirror_y (via scale)
- Positions for feed_to_end

### Origin Position Transform (`inkcut/device/plugin.py`)
```python
origin_transform = QtGui.QTransform()
if device.config.origin_position == 'bottom_right':
    origin_transform.translate(-width, 0)
elif device.config.origin_position == 'top_left':
    origin_transform.translate(0, -height)
elif device.config.origin_position == 'top_right':
    origin_transform.translate(-width, -height)
```
- Currently applied in live preview only
- Needs to be applied in main preview too

---

## Key Files and Their Roles

| File | Role | Transform Type |
|------|------|-----------------|
| `inkcut/preview/plugin.py` | Preview initialization | Y-flip (1, -1) |
| `inkcut/preview/plot_view.py` | Plot item rendering | Y-flip (1, -1) |
| `inkcut/job/plugin.py` | Job preview refresh | ❌ Missing origin transform |
| `inkcut/job/models.py` | Job path creation | Y negation (-y) |
| `inkcut/device/plugin.py` | Device output | Origin, scale, rotate |
| `inkcut/preview/indicators.py` | Visual indicators | Origin position aware |

---

## Coordinate System Decision

### Is Using a Cartesian-like System the Right Choice?

**Yes, with caveats.**

**Advantages**:
- Intuitive for UI/preview (matches mathematical expectations)
- Consistent with design software conventions
- Easier for users to understand

**Disadvantages**:
- Requires Y-flip transformations (small performance cost)
- Mismatch with Qt's native system (adds complexity)
- Device-specific transforms can override it anyway

**Recommendation**: Continue using the Cartesian-like preview system. It's the right choice for UI/visualization. The device output layer can handle device-specific transformations.

---

## The Main Issue: Origin Position Not Applied to Main Preview

### Problem
```
Job Preview                          Live Preview
┌──────────────────┐                ┌──────────────────┐
│ Design at (0,0)  │                │ Design at origin │
│ (bottom-left)    │   ❌ MISMATCH  │ (correct)        │
└──────────────────┘                └──────────────────┘
```

### Root Cause
In `inkcut/job/plugin.py`, the `_refresh_preview()` method doesn't create or apply an `origin_transform`:

```python
# MISSING:
origin_transform = QtGui.QTransform()
if device.config.origin_position == 'bottom_right':
    origin_transform.translate(-width, 0)
# ... etc ...

# Should apply origin_transform to all paths:
path=transform(origin_transform.map(job.move_path))
```

### Solution
Add the origin transformation logic to `_refresh_preview()`, similar to what's already done in `DevicePlugin._reset_preview()`.

---

## Your Summa D760 Configuration

For a Summa D760 with:
- Origin at bottom-right
- Feed direction Y (default)

**Configuration**:
```
origin_position = 'bottom_right'
feed_axis = 'y'
swap_xy = False (or as needed)
mirror_x = False (or as needed)
mirror_y = False (or as needed)
```

**Coordinate Transformation**:
```
1. Design created at (0, 0) [bottom-left in job coordinates]
2. Origin transform applied: translate(-width, 0)
3. Design now at (-width, 0) [bottom-right in preview]
4. Device receives coordinates in device-specific format
```

**What Should Happen**:
- ✓ Design appears at bottom-right in preview
- ✓ Feed direction arrow points downward
- ✓ Feed-after-cut works correctly (needs implementation)

**Current Issue**:
- ✗ Design appears at bottom-left in main preview
- ✓ Design appears at bottom-right in live preview
- ✗ Mismatch between preview and live preview

---

## Implementation Priority

### High Priority (Fixes the Main Issue)
1. **Apply origin transform in job preview** (`inkcut/job/plugin.py`)
   - 10-15 lines of code
   - Fixes the preview mismatch
   - No breaking changes

### Medium Priority (Completes Feature)
2. **Implement feed_to_end for X-axis feed** (`inkcut/device/plugin.py`)
   - 10-20 lines of code
   - Required for X-axis feed devices
   - Needed for feed-after-cut functionality

3. **Add configuration validation** (`inkcut/device/plugin.py`)
   - 5-10 lines of code
   - Prevents invalid configurations
   - Improves user experience

### Low Priority (Polish)
4. **Update documentation** (new file or existing docs)
5. **Add unit tests** (for coordinate transformations)
6. **Add visual feed preview** (animate material feed)

---

## Testing Strategy

### Quick Verification (5 minutes)
1. Open a design in Inkcut
2. Change origin_position to 'bottom_right'
3. Compare main preview with live preview
4. They should show design at same position

### Comprehensive Testing (30 minutes)
1. Test all four origin positions
2. Test with and without swap_xy
3. Test with and without mirror_x/y
4. Test feed_to_end with both X and Y feed axes
5. Verify live preview matches main preview

### Physical Testing (1-2 hours)
1. Load a test design on Summa D760
2. Run cut job and verify:
   - Design cuts at correct location
   - Material feeds in correct direction
   - Feed-after-cut advances material correctly

---

## Coordinate System Glossary

| Term | Definition | Example |
|------|-----------|---------|
| **Qt Native** | PyQtGraph's default coordinate system | Top-left origin, Y down |
| **Y-flip** | Transform that negates Y coordinates | `QTransform.fromScale(1, -1)` |
| **Cartesian** | Standard mathematical coordinates | Bottom-left origin, Y up |
| **Origin Position** | Where the cutter's origin is located | bottom-left, bottom-right, etc. |
| **Feed Direction** | Axis along which material feeds | X or Y |
| **swap_xy** | 90° rotation (swaps X and Y axes) | Rotates design 90° |
| **scale** | Multiplier for X and Y coordinates | (1.06, 1.06) means 6% larger |
| **mirror_x/y** | Flips design along X or Y axis | Reverses design horizontally/vertically |

---

## References

### Documentation Files Created
1. **COORDINATE_SYSTEM_ANALYSIS.md** - Detailed technical analysis
2. **COORDINATE_SYSTEM_DIAGRAMS.md** - Visual representations
3. **IMPLEMENTATION_GUIDE.md** - Step-by-step implementation instructions
4. **COORDINATE_SYSTEM_SUMMARY.md** - This file

### Key Source Files
- `inkcut/preview/plugin.py` - Preview layer transforms
- `inkcut/job/plugin.py` - Job preview (needs origin transform)
- `inkcut/device/plugin.py` - Device output transforms
- `inkcut/preview/indicators.py` - Visual indicators
- `inkcut/device/view.enaml` - UI configuration

---

## Conclusion

Inkcut uses a **hybrid coordinate system** that's appropriate for its use case:
- The **preview/UI layer** uses Cartesian-like coordinates (bottom-left origin, Y up)
- The **device output layer** uses device-specific coordinates
- Y-flip transformations convert between Qt's native system and the preview system

The main issue is that **origin position transformation is applied in the live preview but not in the main preview**, causing a mismatch. This is a simple fix that requires adding about 10-15 lines of code to `inkcut/job/plugin.py`.

The coordinate system design is sound and should be maintained. Once the origin position transform is applied consistently, your Summa D760 with bottom-right origin should work correctly.
