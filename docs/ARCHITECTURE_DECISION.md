# Architectural Decision: Origin Position & Feed Direction UI

## The Question

Should the new UI controls for `origin_position` and `feed_axis` replace the existing low-level settings (`swap_xy`, `mirror_x`, `mirror_y`), or should both coexist?

## Quick Answer

**Keep both.** They serve different purposes and operate at different levels of abstraction. Your UI choice is architecturally sound.

---

## The Distinction: Two Levels of Abstraction

### Level 1: High-Level User Configuration (NEW - Your UI)

**What the user thinks about:**
- "My device's origin is at the bottom-right"
- "My device feeds material in the X direction"

**Settings:**
- `origin_position`: bottom_left, bottom_right, top_left, top_right
- `feed_axis`: x, y

**Purpose:**
- User-friendly way to describe physical device characteristics
- Directly observable on the actual hardware
- Affects preview visualization and design positioning

**Implementation:**
- Applied as translation transforms in preview and device layers
- Shifts the entire design to the correct quadrant
- Affects `feed_to_end` calculations

### Level 2: Low-Level Protocol Configuration (EXISTING - Keep These)

**What the device protocol needs:**
- "I need coordinates with X and Y swapped"
- "I need the X axis mirrored"
- "I need both axes mirrored and scaled"

**Settings:**
- `swap_xy`: Rotate 90° (swap axes) + scale(-1, 1)
- `mirror_x`: Scale(-1, 1) - flip X axis
- `mirror_y`: Scale(1, -1) - flip Y axis
- `scale`: Custom scaling factors
- `rotation`: Final rotation (0, 90, -90)

**Purpose:**
- Describe the exact coordinate transformation needed for the device protocol
- Protocol-specific, not user-facing
- Set via `default_config` in device driver definitions
- Can't be derived from `origin_position` and `feed_axis` alone

**Implementation:**
- Applied in `Device.init()` to transform the job model
- Directly affects what coordinates are sent to the device

---

## Why They're Not Equivalent

### Example 1: Roland PNC-900

```python
# Device driver definition:
DeviceDriver:
    manufacturer = 'Roland'
    model = 'PNC-900'
    width = '12in'
    protocols = ['camm-gl1']
    # No special config - uses defaults
```

- `origin_position`: bottom_left (default)
- `feed_axis`: y (default)
- `swap_xy`: False
- `mirror_x`: False
- `mirror_y`: False

**Interpretation:** This device expects standard Cartesian coordinates (bottom-left origin, Y feed).

### Example 2: Roland Stika SV-15

```python
# Device driver definition:
DeviceDriver:
    manufacturer = 'Roland'
    model = 'Stika SV-15'
    width = '15in'
    protocols = ['hpgl']
    default_config = {
      'swap_xy': True
    }
```

- `origin_position`: bottom_left (user configurable)
- `feed_axis`: y (user configurable)
- `swap_xy`: True (protocol requirement)
- `mirror_x`: False
- `mirror_y`: False

**Interpretation:** The HPGL protocol used by this device requires X and Y to be swapped. This is independent of where the user wants their origin to be.

### Example 3: Hypothetical Device with Unusual Protocol

```python
DeviceDriver:
    manufacturer = 'Custom'
    model = 'Special Cutter'
    width = '24in'
    default_config = {
      'scale': [ 5.64, 5.64 ],
      'swap_xy': True,
      'mirror_x': True,
      'mirror_y': True
    }
```

- `origin_position`: bottom_left (user configurable)
- `feed_axis`: y (user configurable)
- `swap_xy`: True (protocol requirement)
- `mirror_x`: True (protocol requirement)
- `mirror_y`: True (protocol requirement)
- `scale`: [5.64, 5.64] (protocol requirement)

**Interpretation:** This device has a very unusual protocol that requires coordinates to be transformed in a specific way. The user can still choose their preferred origin and feed direction, which will be applied on top of these protocol transforms.

---

## The Transformation Pipeline

```
SVG Input
    ↓
Job.create() with swap_xy and scale from device config
    ↓ [Low-level protocol transforms applied]
    ↓
Device model (in device protocol coordinates)
    ↓
Preview display with origin_position and feed_axis transforms
    ↓ [High-level user transforms applied]
    ↓
Design shown at correct position in preview
    ↓
Device.transform() with final scale and rotation
    ↓
Device protocol handler
    ↓
Physical device
```

The key insight: **`swap_xy` and `mirror_x/y` are applied BEFORE `origin_position`.**

- `swap_xy`, `mirror_x/y` transform the coordinate system itself
- `origin_position` shifts the design within that transformed coordinate system

---

## Why `swap_xy` Can't Be Derived from `origin_position`

### Scenario: User wants origin at bottom-right with Y feed

**What they might think:**
"I just need to mirror the X axis, so I'll set `mirror_x = True`"

**Why that's wrong:**
The actual device might already have `swap_xy = True` in its driver config. Setting `mirror_x = True` on top of that would:
1. Rotate the design 90° (swap_xy)
2. Mirror it on X axis
3. Result: Design is in the wrong orientation

**What should happen instead:**
- User sets `origin_position = bottom_right` and `feed_axis = y`
- Device driver already has `swap_xy = True` configured
- Preview applies origin_position transform to shift design to bottom-right
- Device receives coordinates with both transforms applied correctly

### Scenario: User wants origin at top-left with X feed

**User expectation:**
"I need to move the origin up and swap axes"

**Actual implementation:**
- User sets `origin_position = top_left` and `feed_axis = x`
- Device driver's `swap_xy` setting (if any) is already configured
- Preview applies origin_position transform to shift design up
- Feed direction indicator points in X direction
- Device receives coordinates with protocol transforms intact

---

## Why Your UI Placement is Correct

You put `origin_position` and `feed_axis` in the device UI. This is correct because:

1. **They're device characteristics**, not job characteristics
2. **They're observable on the hardware** - users can see where their device's origin is
3. **They're persistent per device** - each device has its own origin and feed direction
4. **They affect device output**, not just preview

However, they operate at a different level than `swap_xy`, `mirror_x/y`:
- Those are **protocol transforms** (how to convert to device protocol coordinates)
- These are **physical characteristics** (where the device's origin is and how it feeds)

---

## The Current Gap: Origin Transform Not Applied to Device Output

There's currently a gap in the implementation:

**What's implemented:**
- ✅ `origin_position` UI in device config
- ✅ `feed_axis` UI in device config
- ✅ Visual indicators in preview
- ✅ Origin transform applied in live preview

**What's missing:**
- ❌ Origin transform applied to main job preview
- ❌ Origin transform applied to device output
- ❌ Feed direction affects `feed_to_end` calculation

The origin transform should be applied:
1. In the job preview (for consistency with live preview)
2. In the device output (so device receives coordinates at the correct origin)

Currently it's only in the live preview, which is why you see the mismatch.

---

## Recommended Implementation

### Keep All Settings:

```python
class DeviceConfig(Model):
    # High-level user configuration (your UI)
    origin_position = Enum('bottom_left', 'bottom_right', 'top_left', 'top_right')
    feed_axis = Enum('x', 'y')

    # Low-level protocol configuration (existing)
    swap_xy = Bool()
    mirror_x = Bool()
    mirror_y = Bool()
    scale = ContainerList(Float())
    rotation = Enum(0, 90, -90)
```

### Apply Transforms in This Order:

1. **In `Device.init()`** (protocol transforms):
   ```python
   scale = config.scale[:]
   if config.mirror_x:
       scale[0] *= -1
   if config.mirror_y:
       scale[1] *= -1
   model = job.create(swap_xy=config.swap_xy, scale=scale)
   ```

2. **In Preview** (user transforms):
   ```python
   origin_transform = QtGui.QTransform()
   if config.origin_position == 'bottom_right':
       origin_transform.translate(-width, 0)
   # ... apply to all paths ...
   ```

3. **In Device Output** (final transforms):
   ```python
   t = QtGui.QTransform()
   if config.scale:
       t.scale(*config.scale)
   if config.rotation:
       t.rotate(config.rotation)
   ```

### For Different Device Types:

**Type A: Simple devices (e.g., Roland PNC)**
- User configures: `origin_position`, `feed_axis`
- Device driver sets: nothing (all defaults)
- Works perfectly with your UI

**Type B: Devices with unusual protocols (e.g., Roland Stika)**
- User configures: `origin_position`, `feed_axis`
- Device driver sets: `swap_xy = True`
- Both transforms work together correctly

**Type C: Devices with custom transforms**
- User configures: `origin_position`, `feed_axis`
- Device driver sets: `swap_xy`, `mirror_x`, `mirror_y`, `scale`
- Both transforms work together correctly

---

## Why Not Replace `swap_xy` with `origin_position`?

### Reason 1: They Serve Different Purposes

`swap_xy` describes a **protocol requirement**, not a physical characteristic.

Example: The HPGL protocol might require X and Y to be swapped. This isn't something the user observes on the device - it's how the protocol works.

### Reason 2: They're Not Interchangeable

You can't determine `swap_xy` from `origin_position` and `feed_axis` alone.

- User says: "My origin is bottom-right, feed is Y"
- This doesn't tell you if the protocol needs `swap_xy`
- Different devices with the same origin/feed might need different `swap_xy` values

### Reason 3: Advanced Users Need Low-Level Control

Some users might need to fine-tune the coordinate transforms beyond what your UI provides.

Example: "My device needs X and Y swapped, but my origin is actually at the center, not a corner"

Your UI provides the common cases, but `swap_xy` provides escape hatches for unusual devices.

### Reason 4: Device Drivers Already Use These

Existing device drivers specify `swap_xy`, `mirror_x`, `mirror_y` in their configs.

Removing these would break existing device definitions and require migration.

---

## The Architecture is Sound

Your approach is correct:

1. **Add high-level UI** for `origin_position` and `feed_axis` ✅
2. **Keep low-level settings** for `swap_xy`, `mirror_x`, `mirror_y` ✅
3. **Apply both transforms** in the correct order ✅
4. **Document the relationship** between them ✅

This creates a flexible system where:
- Most users use your intuitive UI
- Device drivers can specify protocol-specific transforms
- Advanced users can fine-tune if needed
- Everything works together correctly

---

## Summary

| Aspect | swap_xy, mirror_x/y | origin_position, feed_axis |
|--------|---------------------|---------------------------|
| **Purpose** | Protocol transforms | Physical characteristics |
| **User-facing** | No (device driver only) | Yes (your UI) |
| **Observable** | No (protocol detail) | Yes (on the device) |
| **Applied where** | Device.init() | Preview + Device output |
| **Configurable by** | Device driver | User |
| **Can be replaced** | No | No |
| **Level of abstraction** | Low (protocol) | High (physical) |

**Recommendation: Keep both.** They're complementary, not redundant. Your UI is at the right level of abstraction and doesn't make the device layer more complex - it actually makes it more user-friendly while preserving the flexibility for device-specific needs.
