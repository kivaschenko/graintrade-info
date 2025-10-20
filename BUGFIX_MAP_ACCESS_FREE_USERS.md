# Bug Fix: Map Access Error for Free Plan Users

## Issue
When free plan users entered an address in the ItemForm, they encountered a JavaScript error:
```
ERROR: can't access property "flyTo", this.map is null
```

## Root Cause
The `handleAddressInput()` method was attempting to call `this.map.flyTo()` without checking if the map object exists. For free plan users, `this.map` is `null` because we don't initialize the Mapbox map for them (to save API costs).

## Fix Applied

### File: `frontend/src/components/ItemForm.vue`

#### 1. Fixed `handleAddressInput()` method (line ~497)
**Before:**
```javascript
// Reset map to default view
this.map.flyTo({ center: [31.946946, 49.305825], zoom: 5 });
```

**After:**
```javascript
// Reset map to default view (only if map exists - paid users only)
if (this.map && this.hasMapAccess) {
  this.map.flyTo({ center: [31.946946, 49.305825], zoom: 5 });
}
```

#### 2. Added defensive check to resize listener (line ~357)
**Before:**
```javascript
window.addEventListener('resize', () => {
  this.map.resize();
});
```

**After:**
```javascript
window.addEventListener('resize', () => {
  if (this.map) {
    this.map.resize();
  }
});
```

## Verification

All map access operations now check if the map exists:

1. ✅ `handleAddressInput()` - Checks `this.map && this.hasMapAccess` before calling `flyTo()`
2. ✅ `updateMapPreview()` - Already had check `this.hasMapAccess && this.map` before updating map
3. ✅ Window resize listener - Now checks `if (this.map)` before calling `resize()`

## Expected Behavior After Fix

### Free Plan Users:
- ✅ Can enter addresses without errors
- ✅ Address is geocoded using Nominatim
- ✅ Country, region, and coordinates are filled automatically
- ✅ No map operations are attempted
- ✅ See informative card encouraging upgrade

### Paid Plan Users:
- ✅ Map loads and displays normally
- ✅ Map updates as they type address
- ✅ Marker is added/updated on map
- ✅ Map flies to location when found

## Testing Steps

1. **Test as Free User:**
   - Login with a free plan account
   - Navigate to `/items/new`
   - Type an address (e.g., "Kyiv, Ukraine")
   - **Expected:** No errors, coordinates filled, no map shown

2. **Test as Paid User:**
   - Login with a basic/premium plan account
   - Navigate to `/items/new`
   - Type an address
   - **Expected:** Map loads, updates, and shows location

## Related Changes
- See `ITEMFORM_ACCESS_AND_MAP_RESTRICTIONS.md` for the original implementation
- This fix ensures the implementation works correctly for free users
