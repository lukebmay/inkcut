# Inkcut Coordinate System Analysis

## Executive Summary

Inkcut does **NOT** use a pure Cartesian coordinate system throughout. Instead, it uses **Qt's native coordinate system with strategic Y-axis flips applied at multiple layers** to create a bottom-up coordinate system for the UI while maintaining compatibility with device protocols.

### Key Finding
The coordinate system is **layered and context-dependent**:
1. **Qt Native Layer**: Top-left origin, Y increases downward
2. **Preview/UI Layer**: Bottom-left origin (after Y-flip), Y increases upward
3. **Device Output Layer**: Device-specific, determined by `swap_xy`, `mirror_x`, `mirror_y`, `scale`, and `rotation` settings

---

## Detailed Coordinate System Analysis

### Layer 1: Qt Native Coordinate System

**Location**: PyQtGraph library (Qt's native system)

- **Origin**: Top-left corner (0, 0)
- **X-axis**: Increases to the right
- **Y-axis**: Increases downward
- **Usage**: Internal to PyQtGraph rendering

### Layer 2: Inkcut Preview/UI Layer

**Location**: `inkcut/preview/plugin.py` (PreviewPlugin class)

```python
def _default_transform(self):
    """ Qt displays top to bottom so this can be used to flip it. """
    return QtGui.QTransform.fromScale(1, -1)
```

**Coordinate System After Transform**:
- **Origin**: Bottom-left corner (0, 0)
- **X-axis**: Increases to the right
- **Y-axis**: Increases upward (Cartesian-like)
- **Implementation**: Y-flip applied via `QTransform.fromScale(1, -1)`

**Where this transform is applied**:
1. In `inkcut/preview/plot_view.py` - `PainterPathPlotItem.updateData()`:
   ```python
   self.path = QtGui.QTransform.fromScale(1, -1).map(path)
   ```

2. In `inkcut/preview/plugin.py` - `PreviewModel.update()`:
   ```python
   self.paths[0].lineTo(x, -y)  # Direct Y negation
   ```

3. In `inkcut/job/models.py` - `Job.create()`:
   ```python
   model.addPath(QTransform.fromTranslate(x, -y).map(path))
   ```

### Layer 3: Job Processing Layer

**Location**: `inkcut/job/models.py` (Job.create() method)

The job processing applies transformations in this order:
1. **Copy positioning**: Translates copies using `(x, -y)` coordinates
2. **Scaling**: Applied via `scale` parameter
3. **Rotation**: Applied via `swap_xy` (90° rotation)
4. **Alignment**: Centers or pads the design based on material dimensions
5. **Feed-to-end**: Positions the design so the feed endpoint is at a specific location

**Key code snippet**:
```python
# Move to 0,0 (bottom-left)
bbox = model.boundingRect()
p = bbox.bottomLeft()
tx, ty = -p.x(), -p.y()

# Apply padding and alignment
tx += px
ty += py

model = QTransform.fromTranslate(tx, ty).map(model)
```

### Layer 4: Device Output Layer

**Location**: `inkcut/device/plugin.py` (Device class)

The device applies final transformations:

```python
def transform(self, path):
    """ Apply the device output transform to the given path. """
    config = self.config
    t = QtGui.QTransform()

    if config.scale:
        t.scale(*config.scale)

    if config.rotation:
        t.rotate(config.rotation)

    path = t.map(path)
    return path
```

And in the `init()` method:
```python
scale = config.scale[:]
if config.mirror_x:
    scale[0] *= -1
if config.mirror_y:
    scale[1] *= -1

model = job.create(swap_xy=config.swap_xy, scale=scale)

if job.feed_to_end:
    x, y, z = self.origin
    model.translate(x, -y)  # Note: Y is negated
```

---

## Origin Position Handling (Current Implementation)

**Location**: `inkcut/device/plugin.py` - `DevicePlugin._reset_preview()` method (lines 1295-1310)

The device plugin already has origin position transformation logic:

```python
origin_transform = QtGui.QTransform()
if device.config.origin_position == 'bottom_right':
    origin_transform.translate(-width, 0)
elif device.config.origin_position == 'top_left':
    origin_transform.translate(0, -height)
elif device.config.origin_position == 'top_right':
    origin_transform.translate(-width, -height)
# bottom_left needs no shift
```

**Current Status**:
- ✅ The origin indicator is displayed correctly
- ✅ The feed direction indicator is displayed correctly
- ✅ The origin position transform is applied in the live preview
- ❌ **The design itself is NOT shifted in the main job preview** (this is the issue)

---

## Coordinate Flow Diagram

```
SVG Document (from Inkscape)
    ↓
Job.create() [Qt bottom-left, Y-flipped coordinates]
    ├─ Applies swap_xy (90° rotation)
    ├─ Applies scale
    ├─ Aligns to material
    └─ Returns QPainterPath in job coordinates
    ↓
Device.init() [Applies device-specific transforms]
    ├─ Applies mirror_x, mirror_y via scale
    ├─ Applies swap_xy (if needed)
    ├─ Applies feed_to_end translation
    └─ Returns QPainterPath in device coordinates
    ↓
Device.transform() [Final output transforms]
    ├─ Applies scale
    ├─ Applies rotation
    └─ Returns QPainterPath ready for device protocol
    ↓
Device Protocol Handler (HPGL, CAMM-GL, etc.)
    Sends coordinates to physical device
```

---

## Analysis: Is Inkcut Using Cartesian Coordinates?

### Answer: **Partially, but with important caveats**

**What IS Cartesian-like**:
- ✅ The preview/UI uses a Cartesian-like system (bottom-left origin, Y increases upward)
- ✅ Within the preview, you can think in standard mathematical coordinates
- ✅ The design is positioned assuming bottom-left origin by default

**What is NOT Cartesian**:
- ❌ The underlying Qt system is top-down
- ❌ Multiple Y-flip transformations are applied at different layers
- ❌ Device-specific transformations (swap_xy, mirror_x, mirror_y) can completely change the coordinate system
- ❌ The coordinate system is context-dependent (preview vs. device output)

### Why This Design?

1. **Qt Compatibility**: Qt uses top-left origin natively, so flips are necessary
2. **Device Compatibility**: Different devices have different origins and feed directions, so the design needs to be flexible
3. **Hardware Abstraction**: The device layer abstracts away hardware-specific coordinate systems

---

## Current Issue: Origin Position Not Applied to Main Preview

**Problem Location**: `inkcut/job/plugin.py` - `JobPlugin._refresh_preview()` method

The job plugin's preview refresh does NOT apply the origin position transformation:

```python
def _refresh_preview(self, change):
    """Redraw the preview on the screen"""
    # ... setup code ...

    # Apply the final output transforms from the device
    transform = device.transform if device else lambda p: p

    if job.model:
        view_items.extend([
            dict(path=transform(job.move_path), pen=plot.pen_up),
            dict(path=transform(job.cut_path), pen=plot.pen_down),
        ])

    # Missing: origin_position transformation!
```

**Contrast with Device Plugin**: `inkcut/device/plugin.py` - `DevicePlugin._reset_preview()` method

The device plugin DOES apply origin position transformation:

```python
origin_transform = QtGui.QTransform()
# ... build origin_transform based on origin_position ...

view_items.append(
    dict(path=device.transform(origin_transform.map(r.map(t.map(device.area.path)))),
         pen=plot.pen_device,
         skip_autorange=True))
```

---

## Recommendation for Origin Position Support

### Approach 1: **Apply Origin Transform in Job Plugin Preview** (RECOMMENDED)

This is the most consistent approach:

1. In `inkcut/job/plugin.py`, modify `_refresh_preview()` to:
   - Get the device's origin_position and feed_axis
   - Build an origin_transform based on the device dimensions and origin position
   - Apply this transform to the job paths before sending to the preview

2. The transform should work as follows:
   ```
   For bottom_left (default): No translation needed
   For bottom_right: Translate by (-width, 0)
   For top_left: Translate by (0, -height)
   For top_right: Translate by (-width, -height)
   ```

3. This keeps the main preview consistent with the live preview

### Approach 2: Apply Origin Transform in Device Layer

Alternatively, apply the origin transform in `Device.init()` or `Device.transform()`:
- Less preferred because it mixes device configuration with job processing
- Would require careful handling of the coordinate system flips

### Approach 3: Use a Unified Coordinate Transformation System

Create a centralized coordinate transformation system that:
- Handles all coordinate system conversions
- Applies origin position, feed direction, and device-specific transforms
- Used by both preview and device layers
- More complex but more maintainable long-term

---

## Key Observations About Y-Coordinate Negation

Throughout the codebase, you'll see `-y` applied in several places:

1. **In Preview Updates**: `self.paths[0].lineTo(x, -y)`
2. **In Job Processing**: `QTransform.fromTranslate(x, -y)`
3. **In Device Init**: `model.translate(x, -y)`

This is because:
- The preview system expects bottom-up coordinates (Y increases upward)
- Device positions are often provided in top-down coordinates
- The negation converts between these systems

---

## Feed Direction Handling

The feed direction (X or Y) is currently only used in the indicators but NOT in the actual coordinate transformations. To fully support different feed directions:

1. The feed direction should affect how `feed_to_end` is calculated
2. The feed direction should affect the orientation of the design relative to the material
3. Currently, `feed_to_end` assumes Y-axis feed:
   ```python
   end_point = (QPointF(
       0, -self.feed_after + model.boundingRect().top())
                if self.feed_to_end else QPointF(0, 0))
   ```

For X-axis feed, this would need to be:
   ```python
   end_point = (QPointF(
       self.feed_after + model.boundingRect().left(), 0)
                if self.feed_to_end else QPointF(0, 0))
   ```

---

## Summary Table

| Layer | Origin | X Direction | Y Direction | Notes |
|-------|--------|-------------|-------------|-------|
| Qt Native | Top-left | → | ↓ | PyQtGraph native |
| Inkcut Preview | Bottom-left | → | ↑ | Y-flipped for UI |
| Job Processing | Bottom-left | → | ↑ | Uses Y negation |
| Device Output | Configurable | Configurable | Configurable | Via swap_xy, mirror_x/y |

---

## Conclusion

Inkcut uses a **hybrid coordinate system**:
- The **UI/Preview layer** uses a Cartesian-like system with bottom-left origin
- The **underlying Qt layer** uses top-down coordinates with Y-flips to convert
- The **device layer** applies device-specific transformations

To properly support different origin positions and feed directions:

1. ✅ **Origin Position**: Apply translation transforms based on device configuration (already done in live preview, needs to be added to main preview)
2. ⚠️ **Feed Direction**: Currently only visual indicators; needs implementation in coordinate transformations
3. ✅ **Coordinate System**: The existing Cartesian-like preview system is appropriate and should be maintained

The recommendation is to **apply origin position transforms in the job preview layer** to keep the main preview consistent with the live preview.
