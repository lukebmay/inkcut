# Origin Transform Implementation: Where and How

## Current Status

The origin position transformation is partially implemented:

| Component | Status | Location |
|-----------|--------|----------|
| UI Controls | ✅ Complete | `inkcut/device/view.enaml` |
| Visual Indicators | ✅ Complete | `inkcut/preview/indicators.py` |
| Live Preview | ✅ Complete | `inkcut/device/plugin.py` (_reset_preview) |
| Main Preview | ❌ Missing | `inkcut/job/plugin.py` (_refresh_preview) |
| Device Output | ❌ Unclear | `inkcut/device/plugin.py` (init) |

---

## The Problem: Incomplete Implementation

Currently, the origin transform is only applied in the **live preview**, not in:
1. The **main job preview** (what users see when designing)
2. The **device output** (what actually gets sent to the device)

This causes:
- **Mismatch between main and live preview**: Design appears at different positions
- **Potential device output issues**: Device might not receive coordinates at the correct origin

---

## Solution: Apply Origin Transform in Multiple Places

### 1. Main Job Preview (HIGH PRIORITY)

**File**: `inkcut/job/plugin.py`
**Method**: `_refresh_preview()`
**Why**: Consistency with live preview

**Current Code** (lines ~182-240):
```python
def _refresh_preview(self, change):
    """Redraw the preview on the screen"""
    view_items = []

    preview_plugin = self.workbench.get_plugin("inkcut.preview")
    job = self.job
    plot = preview_plugin.preview
    t = preview_plugin.transform

    plugin = self.workbench.get_plugin("inkcut.device")
    device = plugin.device

    transform = device.transform if device else lambda p: p

    if device and device.area:
        area = device.area
        view_items.append(
            dict(
                path=transform(t.map(device.area.path)),
                pen=plot.pen_device,
                skip_autorange=True,
            )
        )

    if job.model:
        view_items.extend([
            dict(path=transform(job.move_path), pen=plot.pen_up),
            dict(path=transform(job.cut_path), pen=plot.pen_down),
        ])

    if job.material:
        view_items.extend([
            dict(
                path=transform(t.map(job.material.path)),
                pen=plot.pen_media,
                skip_autorange=([0, job.size[0]], [0, job.size[1]]),
            ),
            dict(
                path=transform(t.map(job.material.padding_path)),
                pen=plot.pen_media_padding,
                skip_autorange=True,
            ),
        ])

    preview_plugin.set_preview(*view_items, device=device)
```

**Modified Code**:
```python
def _refresh_preview(self, change):
    """Redraw the preview on the screen"""
    view_items = []

    preview_plugin = self.workbench.get_plugin("inkcut.preview")
    job = self.job
    plot = preview_plugin.preview
    t = preview_plugin.transform

    plugin = self.workbench.get_plugin("inkcut.device")
    device = plugin.device

    transform = device.transform if device else lambda p: p

    # NEW: Create origin position transformation
    origin_transform = QtGui.QTransform()
    if device and device.area:
        area = device.area
        width = area.size[0]
        height = area.size[1]

        if device.config.origin_position == 'bottom_right':
            origin_transform.translate(-width, 0)
        elif device.config.origin_position == 'top_left':
            origin_transform.translate(0, -height)
        elif device.config.origin_position == 'top_right':
            origin_transform.translate(-width, -height)
        # bottom_left needs no translation

    if device and device.area:
        area = device.area
        view_items.append(
            dict(
                # MODIFIED: Apply origin_transform
                path=transform(origin_transform.map(t.map(device.area.path))),
                pen=plot.pen_device,
                skip_autorange=True,
            )
        )

    if job.model:
        view_items.extend([
            # MODIFIED: Apply origin_transform
            dict(path=transform(origin_transform.map(job.move_path)), pen=plot.pen_up),
            dict(path=transform(origin_transform.map(job.cut_path)), pen=plot.pen_down),
        ])

    if job.material:
        view_items.extend([
            dict(
                # MODIFIED: Apply origin_transform
                path=transform(origin_transform.map(t.map(job.material.path))),
                pen=plot.pen_media,
                skip_autorange=([0, job.size[0]], [0, job.size[1]]),
            ),
            dict(
                # MODIFIED: Apply origin_transform
                path=transform(origin_transform.map(t.map(job.material.padding_path))),
                pen=plot.pen_media_padding,
                skip_autorange=True,
            ),
        ])

    preview_plugin.set_preview(*view_items, device=device)
```

**Changes**:
- Create `origin_transform` based on device config
- Apply it to all path transformations
- Keep all other logic the same

**Testing**:
```python
# Test case 1: bottom_left (default)
device.config.origin_position = 'bottom_left'
# Design should appear at (0, 0)

# Test case 2: bottom_right
device.config.origin_position = 'bottom_right'
# Design should appear shifted left by width

# Test case 3: top_left
device.config.origin_position = 'top_left'
# Design should appear shifted down by height

# Test case 4: top_right
device.config.origin_position = 'top_right'
# Design should appear shifted left and down
```

---

### 2. Device Output (MEDIUM PRIORITY)

**File**: `inkcut/device/plugin.py`
**Method**: `Device.init()`
**Why**: Ensure device receives coordinates at the correct origin

**Question**: Should origin_position affect the coordinates sent to the device?

**Answer**: **Probably not directly.** Here's why:

1. **Device protocols have their own origin conventions**
   - Some expect origin at bottom-left
   - Some expect origin at top-left
   - Some expect origin at center

2. **`swap_xy`, `mirror_x`, `mirror_y` already handle this**
   - Device drivers specify these based on protocol
   - They transform coordinates to what the protocol expects

3. **`origin_position` is about visualization, not device output**
   - It tells the user where the origin is
   - The device protocol already knows where its origin is

**Recommendation**: Keep `Device.init()` as-is. Don't apply origin_transform there.

**However**: Do apply origin_transform to the `feed_to_end` calculation:

**Current Code** (lines ~590-595):
```python
if job.feed_to_end:
    #: Move the job to the new origin
    x, y, z = self.origin
    model.translate(x, -y)
```

**Modified Code**:
```python
if job.feed_to_end:
    #: Move the job to the new origin
    x, y, z = self.origin

    # Adjust for origin position if needed
    if config.origin_position == 'bottom_right':
        x = -x  # Mirror X
    elif config.origin_position == 'top_left':
        y = -y  # Mirror Y
    elif config.origin_position == 'top_right':
        x = -x
        y = -y  # Mirror both

    model.translate(x, -y)
```

**Why**: The feed_to_end feature moves the material to a specific position after cutting. If the origin is at bottom-right instead of bottom-left, the translation should be adjusted accordingly.

---

### 3. Feed Direction Support (MEDIUM PRIORITY)

**File**: `inkcut/job/models.py`
**Method**: `Job.create()`
**Why**: Support X-axis feed direction

**Current Code** (lines ~475-478):
```python
end_point = (QPointF(
    0, -self.feed_after + model.boundingRect().top())
             if self.feed_to_end else QPointF(0, 0))
model.moveTo(end_point)
```

**Problem**: This assumes Y-axis feed. For X-axis feed, the calculation should be different.

**Solution**: Check the device's feed_axis configuration.

**Challenge**: The `Job` class doesn't have access to device config.

**Options**:

**Option A: Pass feed_axis to job.create()**
```python
# In Device.init():
model = job.create(swap_xy=config.swap_xy, scale=scale, feed_axis=config.feed_axis)

# In Job.create():
def create(self, swap_xy=False, scale=None, feed_axis='y'):
    # ... existing code ...
    if self.feed_to_end:
        bbox = model.boundingRect()
        if feed_axis == 'x':
            end_point = QPointF(self.feed_after + bbox.right(), 0)
        else:  # y-axis
            end_point = QPointF(0, -self.feed_after + bbox.top())
    else:
        end_point = QPointF(0, 0)
    model.moveTo(end_point)
```

**Option B: Move feed_to_end logic to Device.init()**
```python
# In Device.init():
model = job.create(swap_xy=config.swap_xy, scale=scale)

# After model is created:
if job.feed_to_end:
    bbox = model.boundingRect()
    if config.feed_axis == 'x':
        end_point = QPointF(job.feed_after + bbox.right(), 0)
    else:  # y-axis
        end_point = QPointF(0, -job.feed_after + bbox.top())

    # Remove the old moveTo and add the new one
    model = QPainterPath(model)  # Copy
    model.moveTo(end_point)
```

**Recommendation**: Use **Option A** (pass feed_axis to job.create())

**Reasons**:
1. Keeps feed_to_end logic in one place
2. Cleaner separation of concerns
3. Easier to test

---

## Implementation Order

### Phase 1: Fix Main Preview (Do First)
1. Modify `inkcut/job/plugin.py` _refresh_preview()
2. Add origin_transform logic
3. Test with all origin positions
4. **This fixes the main issue**

### Phase 2: Support Feed Direction (Do Second)
1. Modify `inkcut/job/models.py` create()
2. Add feed_axis parameter
3. Implement feed_to_end calculation for X-axis
4. Modify `inkcut/device/plugin.py` init()
5. Pass feed_axis to job.create()
6. Test with both X and Y feed

### Phase 3: Polish (Do Last)
1. Add configuration validation
2. Add unit tests
3. Update documentation
4. Test with physical devices

---

## Code Organization

### Current Transform Order (in preview)
```
1. Qt coordinate system (top-down)
2. Preview transform: Y-flip
3. Origin transform: Translate to correct quadrant
4. Device transform: Scale, rotate
5. Display in preview window
```

### Current Transform Order (in device output)
```
1. Qt coordinate system (top-down)
2. Job.create(): Apply swap_xy, scale
3. Device.init(): Apply feed_to_end
4. Device.transform(): Apply final scale, rotation
5. Device protocol handler
```

### Proposed Transform Order (after implementation)
```
1. Qt coordinate system (top-down)
2. Job.create(): Apply swap_xy, scale, feed_axis
3. Device.init(): Apply feed_to_end (adjusted for origin_position)
4. Device.transform(): Apply final scale, rotation
5. Device protocol handler
```

And for preview:
```
1. Qt coordinate system (top-down)
2. Preview transform: Y-flip
3. Origin transform: Translate to correct quadrant
4. Device transform: Scale, rotate
5. Display in preview window
```

---

## Testing Checklist

### Unit Tests
- [ ] origin_transform calculations for all four positions
- [ ] feed_to_end calculation for X-axis feed
- [ ] feed_to_end calculation for Y-axis feed
- [ ] Combined origin + feed_axis scenarios

### Integration Tests
- [ ] Main preview updates when origin_position changes
- [ ] Live preview updates when origin_position changes
- [ ] Main preview matches live preview
- [ ] Device.init() produces correct output

### Manual Tests
- [ ] Visual: Design at correct position in preview
- [ ] Visual: Feed direction indicator correct
- [ ] Physical: Device cuts at correct location
- [ ] Physical: Material feeds in correct direction
- [ ] Physical: Feed-after-cut works correctly

### Device-Specific Tests
- [ ] Summa D760 (bottom-right origin, Y feed)
- [ ] Roland PNC (bottom-left origin, Y feed)
- [ ] Test device with X feed
- [ ] Test device with top-right origin

---

## Potential Issues

### Issue 1: Transform Applied in Wrong Order

**Symptom**: Design appears flipped or rotated incorrectly

**Solution**: Ensure origin_transform is applied BEFORE device.transform():
```python
# CORRECT:
path=device.transform(origin_transform.map(job.move_path))

# WRONG:
path=origin_transform.map(device.transform(job.move_path))
```

### Issue 2: Feed Direction Not Matching Physical Device

**Symptom**: Material feeds in wrong direction

**Solution**: Verify feed_axis is correctly set and feed_to_end calculation accounts for it

### Issue 3: Material Padding Appears in Wrong Position

**Symptom**: Padding area not aligned with origin

**Solution**: Ensure origin_transform is applied to all paths (material, device area, design)

### Issue 4: Origin Indicator Shows Wrong Position

**Symptom**: Indicator doesn't match design position

**Solution**: Verify OriginIndicator receives correct origin_position from device.config

---

## Summary

To complete the origin position and feed direction support:

1. **Main Preview** (HIGH PRIORITY):
   - Add origin_transform to `_refresh_preview()`
   - ~15 lines of code
   - Fixes the preview mismatch

2. **Feed Direction** (MEDIUM PRIORITY):
   - Pass feed_axis to `job.create()`
   - Implement X-axis feed calculation
   - ~20 lines of code

3. **Polish** (LOW PRIORITY):
   - Add validation and tests
   - Update documentation

The architecture is sound. These changes complete the implementation without breaking existing functionality.
