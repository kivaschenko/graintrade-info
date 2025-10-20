# ItemForm Access Control and Map Restrictions Implementation

## Overview
This document describes the implementation of access control for the ItemForm component and conditional map display based on user subscription/tariff plans.

## Changes Implemented

### 1. Authentication Guard for ItemForm Route

**File:** `frontend/src/router/index.js`

- Added `requiresAuth: true` meta property to the ItemForm route
- Implemented a global navigation guard (`router.beforeEach`) that:
  - Checks if the route requires authentication
  - Redirects unauthenticated users to the login page with a redirect query parameter
  - Preserves the intended destination for post-login redirect

**Impact:** Users must be logged in to access `/items/new` (ItemForm). Unauthenticated users are redirected to `/login?redirect=/items/new`.

### 2. Post-Login Redirect

**File:** `frontend/src/components/UserLogin.vue`

- Updated the `handleLogin` method to check for a redirect query parameter
- After successful login, users are redirected to their intended destination or home page

**Impact:** Improves user experience by taking users to the page they originally wanted to access after login.

### 3. Conditional Map Display Based on Tariff Plan

**File:** `frontend/src/components/ItemForm.vue`

#### Data Properties Added:
- `userSubscription`: Stores the user's subscription information
- `hasMapAccess`: Boolean flag indicating if the user has access to Mapbox map preview
- `isLoadingSubscription`: Loading state for subscription fetch

#### New Method:
- `fetchUserSubscription()`: Fetches the user's subscription from `/subscriptions/user/{user_id}` endpoint
  - Determines map access based on tariff scope
  - Free plan users (`scope === 'free'`) do NOT have map access
  - All paid plans (basic, premium, business, etc.) have map access

#### Updated Lifecycle Hook:
- `mounted()`: 
  - Checks authentication (double-check even with route guard)
  - Fetches user subscription
  - Initializes Mapbox map ONLY if user has map access
  - Fetches categories as before

#### Updated Methods:
- `updateMapPreview()`: 
  - Uses free Nominatim API for geocoding (for ALL users)
  - Updates map preview ONLY if user has map access
  - Free users still get coordinates, country, and region filled automatically

#### Template Changes:
- Map preview card is conditionally rendered based on `hasMapAccess`
- Added information card for free plan users explaining:
  - Map preview is unavailable on free plan
  - Geocoding still works automatically
  - Link to view tariff plans
- Form column width adjusts dynamically:
  - With map: `col-lg-7` (70% width)
  - Without map: `col-lg-12` (100% width)

### 4. Translation Updates

**File:** `frontend/src/i18n.js`

Added new translation keys in both English and Ukrainian:

**English:**
- `upgrade_for_map`: "Map Preview"
- `map_preview_locked`: "Map Preview Unavailable"
- `map_preview_locked_description`: "Upgrade to a paid plan to view location previews on an interactive map."
- `geocoding_still_works`: "Location geocoding still works - your address will be converted to coordinates automatically."
- `view_plans`: "View Tariff Plans"

**Ukrainian:**
- `upgrade_for_map`: "Попередній перегляд карти"
- `map_preview_locked`: "Попередній перегляд карти недоступний"
- `map_preview_locked_description`: "Оновіться до платного тарифу, щоб переглядати місця розташування на інтерактивній карті."
- `geocoding_still_works`: "Геокодування все ще працює - ваша адреса буде автоматично перетворена на координати."
- `view_plans`: "Переглянути тарифні плани"

## Technical Details

### Tariff Plans Structure

Based on the database schema (`postgres-init/init.sql`):

| Plan | Scope | Price | Map Access | Features |
|------|-------|-------|------------|----------|
| Free | `free` | $0 | ❌ No | 5 items, 10 map views, geocoding only |
| Basic | `basic` | $10 | ✅ Yes | 10 items, 100 map views, full map access |
| Premium | `premium` | $30 | ✅ Yes | 400 items, 400 map views, full map access |
| Business | `business` | More | ✅ Yes | Unlimited features |

### API Endpoints Used

1. **Get User Subscription:**
   ```
   GET /subscriptions/user/{user_id}
   Headers: Authorization: Bearer {token}
   Response: SubscriptionInResponse with tarif details
   ```

2. **Nominatim Geocoding (Free):**
   ```
   GET https://nominatim.openstreetmap.org/search
   Params: q={address}, format=json, addressdetails=1, limit=1
   Headers: User-Agent: GrainTrade.info
   ```

### Cost Optimization

1. **Mapbox Map Loading:**
   - Free users: Map NOT loaded at all (saves Mapbox API costs)
   - Paid users: Map loaded once on component mount

2. **Geocoding:**
   - All users: Uses free Nominatim API
   - Backend: Can still use Mapbox geocoding if needed
   - No Mapbox geocoding API calls from frontend

### User Experience

#### Free Plan Users:
1. Must be logged in to access ItemForm
2. See an informative card instead of map preview
3. Can still create offers with automatic geocoding
4. Address is converted to coordinates using Nominatim
5. Encouraged to upgrade for map preview feature

#### Paid Plan Users:
1. Must be logged in to access ItemForm
2. See interactive map preview
3. Map updates as they type address
4. Better visual feedback on location accuracy

## Testing Recommendations

1. **Authentication:**
   - Test accessing `/items/new` without login (should redirect to login)
   - Test login redirect flow
   - Verify redirect preserves intended destination

2. **Map Access:**
   - Test with user on free plan (should see info card, no map)
   - Test with user on basic/premium plan (should see map)
   - Test geocoding works for both free and paid users

3. **Geocoding:**
   - Test address input with valid addresses
   - Verify coordinates are filled automatically
   - Test with international addresses

4. **UI/UX:**
   - Test responsive layout (map column vs full width form)
   - Test loading states
   - Test translations (EN/UA)

## Future Enhancements

1. Show usage statistics (e.g., "3/10 map views used this month")
2. Progressive disclosure: Show teaser of map with blur for free users
3. Add analytics to track conversion from free to paid plans
4. Implement soft limits with warnings before hard limits

## Rollback Plan

If issues arise, revert these files:
1. `frontend/src/router/index.js` - Remove meta.requiresAuth and beforeEach guard
2. `frontend/src/components/ItemForm.vue` - Remove subscription check, always show map
3. `frontend/src/components/UserLogin.vue` - Remove redirect handling
4. `frontend/src/i18n.js` - Remove new translation keys (optional)

## Related Documentation

- See `README_GEOCODING.md` for geocoding implementation details
- See `FREE_GEOCODING_IMPLEMENTATION.md` for Nominatim integration
- See `DEPLOYMENT_CHECKLIST.md` for deployment considerations
