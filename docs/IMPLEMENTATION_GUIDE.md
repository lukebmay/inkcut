# Implementation Guide: Origin Position and Feed Direction Support

## Overview

This guide provides step-by-step instructions for implementing full support for configurable origin positions and feed directions in Inkcut.

## Current Status

### ✅ Already Implemented
1. **UI Controls** (`inkcut/device/view.enaml`):
   - Radio buttons for origin position (bottom-left, bottom-right, top-left, top-right)
   - Radio buttons for feed axis (X, Y)
   - Both are persisted in `DeviceConfig`

2. **Visual Indicators** (`inkcut/preview/indicators.py`):
   - `OriginIndicator`: Displays a dot at the origin with label
   - `FeedDirectionIndicator`: Displays an arrow showing feed direction
   - Both indicators respect the configured origin position and feed axis

3. **Live Preview** (`inkcut/device/plugin.py`):
   - Origin position transform is applied in `DevicePlugin._reset_preview()`
   - Live preview shows design at correct position relative to origin

### ❌ Not Yet Implemented / Issues
1. **Main Job Preview** (`inkcut/job/plugin.py`):
   - Origin position transform NOT applied in `JobPlugin._refresh_preview()`
   - Design appears at bottom-left even when origin is configured differently
   - **This is the primary issue causing the mismatch**

2. **Feed Direction Coordinate Adjustments** (`inkcut/job/models.py`):
   - `feed_to_end` only works with Y-axis feed
   - X-axis feed requires different coordinate calculation
   - Not yet implemented

3. **Device Init Feed Direction** (`inkcut/device/plugin.py`):
   - `Device.init()` doesn't account for different feed directions
   - Needs to calculate feed_to_end endpoint differently based on feed_axis

---

## Step 1: Fix Main Job Preview Origin Position

### File: `inkcut/job/plugin.py`

**Problem**: The `_refresh_preview()` method doesn't apply origin position transformation.

**Solution**: Apply the same origin transformation that's used in the live preview.

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

    # ... rest of method ...
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
        # bottom_left needs no shift

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

    # ... rest of method ...

    # Also apply to material paths
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
```

**Imports needed**: Already imported `QtGui` should be available.

**Testing**:
1. Open a design in Inkcut
2. Change origin position to 'bottom_right'
3. Verify that the design in the main preview shifts to the right (negative X direction)
4. Verify that the live preview matches the main preview
5. Test all four origin positions

---

## Step 2: Implement Feed Direction Support in Job Processing

### File: `inkcut/job/models.py`

**Problem**: `feed_to_end` calculation assumes Y-axis feed.

**Current Code** (lines ~475-478):
```python
end_point = (QPointF(
    0, -self.feed_after + model.boundingRect().top())
             if self.feed_to_end else QPointF(0, 0))
model.moveTo(end_point)
```

**Solution**: Check device feed_axis and calculate endpoint accordingly.

**Modified Code**:
```python
# Determine feed direction from device config
device_feed_axis = 'y'  # Default
if hasattr(self, '_device') and self._device:
    device_feed_axis = self._device.config.feed_axis.lower()

if self.feed_to_end:
    bbox = model.boundingRect()
    if device_feed_axis == 'x':
        # X-axis feed: endpoint is at the right of the design
        end_point = QPointF(
            self.feed_after + bbox.right(), 0)
    else:  # y-axis feed (default)
        # Y-axis feed: endpoint is at the top of the design
        end_point = QPointF(
            0, -self.feed_after + bbox.top())
else:
    end_point = QPointF(0, 0)

model.moveTo(end_point)
```

**Issue**: The `Job` class doesn't currently have access to the device config.

**Alternative Approach**: Move feed_to_end logic to Device.init()

This is actually better because:
1. Feed direction is a device property, not a job property
2. Device.init() already has access to device config
3. Keeps concerns separated (job doesn't need to know about device)

### File: `inkcut/device/plugin.py`

**Modified Device.init() method**:

```python
def init(self, job):
    """ Initialize the job. This should do any final path manipulation
    required by the device (or as specified by the config) and any filters
    should be applied here (overcut, blade offset compensation, etc..).

    The connection is not active at this stage.

    Parameters
    -----------
        job: inkcut.job.models.Job instance
            The job to handle.

    Returns
    --------
        model: QtGui.QPainterPath instance or Deferred that resolves
            to a QPainterPath if heavy processing is needed. This path
            is then interpolated and sent to the device.

    """
    log.debug("device | init {}".format(job))
    config = self.config

    # Set the speed of this device for tracking purposes
    units = config.speed_units.split("/")[0]
    job.info.speed = from_unit(config.speed, units)

    scale = config.scale[:]
    if config.mirror_x:
        scale[0] *= -1 if config.mirror_x else 1
    if config.mirror_y:
        scale[1] *= -1 if config.mirror_y else 1

    # Get the internal QPainterPath "model" transformed to how this
    # device outputs
    model = job.create(swap_xy=config.swap_xy, scale=scale)

    if job.feed_to_end:
        # NEW: Consider feed direction when calculating end point
        bbox = model.boundingRect()
        x, y, z = self.origin

        if config.feed_axis == 'x':
            # X-axis feed: feed after the right edge
            end_x = bbox.right() + job.feed_after
            end_y = -y  # Keep Y at origin
            model.translate(end_x, end_y)
        else:  # y-axis feed (default)
            # Y-axis feed: feed after the top edge
            end_x = -x  # Keep X at origin
            end_y = -y - job.feed_after
            model.translate(end_x, end_y)

    #: TODO: Apply filters here

    #: Return the transformed model
    return model
```

**Testing**:
1. Enable `feed_to_end` in job settings
2. Set feed_axis to 'x'
3. Run a test job and verify material feeds correctly
4. Set feed_axis to 'y'
5. Run a test job and verify material feeds correctly

---

## Step 3: Verify Origin Position Works with Feed Direction

### File: `inkcut/device/plugin.py` (Device.init())

**Consideration**: When both origin_position and feed_direction are configured, they should work together.

**Current Implementation**: Origin position is applied in preview only, not in device.init()

**Decision**: Keep origin_position transform in preview layer only, because:
1. Origin position is primarily a visualization concern
2. Device protocols handle their own coordinate systems
3. The device.init() method should work with the job's coordinate system as-is

**However**: The feed_to_end calculation might need adjustment based on origin_position.

**Modified Code** (if needed):
```python
if job.feed_to_end:
    bbox = model.boundingRect()
    x, y, z = self.origin

    # Adjust for origin position
    if config.origin_position == 'bottom_right':
        # Origin is at bottom-right, so X is mirrored
        x = -x
    elif config.origin_position == 'top_left':
        # Origin is at top-left, so Y is mirrored
        y = -y
    elif config.origin_position == 'top_right':
        # Origin is at top-right, so both are mirrored
        x = -x
        y = -y

    if config.feed_axis == 'x':
        end_x = bbox.right() + job.feed_after
        end_y = -y
        model.translate(end_x, end_y)
    else:  # y-axis feed
        end_x = -x
        end_y = -y - job.feed_after
        model.translate(end_x, end_y)
```

**Testing**:
1. Test all combinations of origin_position and feed_axis
2. Verify feed_to_end works correctly in each case
3. Run actual cut jobs to verify physical device behavior

---

## Step 4: Update Live Preview to Show Origin and Feed Indicators

### File: `inkcut/device/plugin.py` (DevicePlugin._reset_preview())

**Status**: Already implemented, but verify it's working correctly.

**Testing**:
1. Open a design
2. Switch to the "Live" preview tab
3. Verify origin indicator appears at configured origin position
4. Verify feed direction arrow points in correct direction
5. Change origin_position and feed_axis settings
6. Verify indicators update in real-time

---

## Step 5: Add Configuration Validation

### File: `inkcut/device/plugin.py` (DeviceConfig class)

**Consideration**: Ensure origin_position and feed_axis values are valid.

**Current Code**: Likely has simple Str() members without validation.

**Enhancement**:
```python
from atom.api import Enum

class DeviceConfig(Model):
    # ... existing members ...

    origin_position = d_(Enum('bottom_left', 'bottom_right', 'top_left', 'top_right')).tag(config=True)
    feed_axis = d_(Enum('x', 'y')).tag(config=True)
```

**Benefits**:
1. Prevents invalid values from being set
2. Provides clear documentation of valid values
3. UI can use these values to populate dropdowns

---

## Step 6: Documentation and User Guide

### Create: `docs/ORIGIN_POSITION_GUIDE.md`

**Content**:
1. Explanation of origin positions
2. How to determine correct origin for your device
3. Feed direction explanation
4. Summa D760 configuration example
5. Troubleshooting common issues

---

## Testing Checklist

### Unit Tests
- [ ] Origin transform calculations for all four positions
- [ ] Feed direction calculations for X and Y axes
- [ ] Combined origin + feed direction scenarios

### Integration Tests
- [ ] Preview updates when origin_position changes
- [ ] Preview updates when feed_axis changes
- [ ] Live preview matches main preview
- [ ] Device.init() produces correct output coordinates

### Manual Tests
- [ ] Visual verification: Design appears at correct position
- [ ] Physical test: Device cuts at correct location
- [ ] Physical test: Material feeds in correct direction
- [ ] Physical test: Feed-after-cut works correctly

### Device-Specific Tests
- [ ] Summa D760 (bottom-right origin, Y feed)
- [ ] Roland PNC (bottom-left origin, Y feed)
- [ ] Custom device with X feed
- [ ] Custom device with top-right origin

---

## Code Review Checklist

- [ ] All Y-coordinate negations are correct
- [ ] Origin transforms applied in both main and live previews
- [ ] Feed direction logic accounts for all combinations
- [ ] No breaking changes to existing functionality
- [ ] Code follows existing style and conventions
- [ ] Comments explain coordinate system assumptions
- [ ] Error handling for invalid configurations

---

## Potential Issues and Solutions

### Issue 1: Design appears flipped in preview

**Cause**: Y-flip applied twice
**Solution**: Check that origin_transform is applied BEFORE preview transform, not after

**Code Pattern (CORRECT)**:
```python
# Apply origin transform first, then preview transform
path = transform(origin_transform.map(path))
```

**Code Pattern (WRONG)**:
```python
# Don't apply in reverse order
path = origin_transform.map(transform(path))
```

### Issue 2: Feed direction doesn't match physical device

**Cause**: Feed direction logic not accounting for origin position
**Solution**: May need to swap X and Y in feed_to_end calculation based on origin

### Issue 3: Material padding appears in wrong position

**Cause**: Origin transform not applied to material padding path
**Solution**: Ensure origin_transform is applied to all paths (material, device area, design)

### Issue 4: Origin indicator shows wrong position

**Cause**: Indicator position not updated when origin_position changes
**Solution**: Verify OriginIndicator receives correct origin_position from device config

---

## Performance Considerations

- Origin transforms are simple translations (minimal performance impact)
- No additional rendering needed (uses existing transform pipeline)
- Live preview performance should be unaffected

---

## Backward Compatibility

- Default origin_position is 'bottom_left' (existing behavior)
- Default feed_axis is 'y' (existing behavior)
- Existing configurations will continue to work without changes
- No breaking changes to API

---

## Future Enhancements

1. **Rotation Support**: Add support for 90°/180°/270° rotation
2. **Custom Origin**: Allow specifying origin at arbitrary coordinates
3. **Origin Visualization**: Show grid aligned to origin position
4. **Feed Preview**: Animate material feed direction during preview
5. **Device Profiles**: Save and load device configurations

---

## References

- `inkcut/job/plugin.py`: Job preview refresh
- `inkcut/device/plugin.py`: Device initialization and live preview
- `inkcut/preview/plugin.py`: Preview transformation
- `inkcut/preview/indicators.py`: Origin and feed indicators
- `inkcut/device/view.enaml`: Device configuration UI
