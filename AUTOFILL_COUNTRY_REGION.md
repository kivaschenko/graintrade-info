# 📍 Auto-fill Country & Region from Nominatim

## Як працює автозаповнення

Коли користувач вводить адресу в полі "Address", frontend автоматично:

1. ⏱️ Чекає 1 секунду після останнього введення (debounce)
2. 🌍 Відправляє запит до Nominatim API
3. 📍 Отримує координати та деталі адреси
4. ✅ Автоматично заповнює поля `country` та `region`
5. 🗺️ Показує місцезнаходження на карті

## Приклади відповідей Nominatim

### Приклад 1: Київ, Україна

**Запит:**
```
https://nominatim.openstreetmap.org/search?q=Kyiv,%20Ukraine&format=json&addressdetails=1&limit=1
```

**Відповідь:**
```json
[
  {
    "lat": "50.4501",
    "lon": "30.5234",
    "display_name": "Kyiv, Ukraine",
    "address": {
      "city": "Kyiv",
      "state": "Kyiv City",
      "country": "Ukraine",
      "country_code": "ua"
    }
  }
]
```

**Заповнення полів:**
- `country` = "Ukraine"
- `region` = "Kyiv City"
- `latitude` = 50.4501
- `longitude` = 30.5234

### Приклад 2: Одеса

**Запит:**
```
https://nominatim.openstreetmap.org/search?q=Odesa&format=json&addressdetails=1&limit=1
```

**Відповідь:**
```json
[
  {
    "lat": "46.4825",
    "lon": "30.7233",
    "display_name": "Odesa, Odesa Oblast, Ukraine",
    "address": {
      "city": "Odesa",
      "state": "Odesa Oblast",
      "country": "Ukraine",
      "country_code": "ua"
    }
  }
]
```

**Заповнення полів:**
- `country` = "Ukraine"
- `region` = "Odesa Oblast"

### Приклад 3: Вулиця в Києві

**Запит:**
```
https://nominatim.openstreetmap.org/search?q=вулиця%20Хрещатик,%20Київ&format=json&addressdetails=1&limit=1
```

**Відповідь:**
```json
[
  {
    "lat": "50.4474",
    "lon": "30.5239",
    "display_name": "Khreshchatyk Street, Kyiv, Ukraine",
    "address": {
      "road": "Khreshchatyk Street",
      "city": "Kyiv",
      "state": "Kyiv City",
      "country": "Ukraine",
      "country_code": "ua"
    }
  }
]
```

**Заповнення полів:**
- `country` = "Ukraine"
- `region` = "Kyiv City"

## Структура address об'єкта Nominatim

Nominatim повертає різні поля в залежності від типу місця:

```javascript
{
  address: {
    // Країна (завжди є)
    country: "Ukraine",
    country_code: "ua",
    
    // Адміністративні одиниці (залежить від місця)
    state: "Kyiv City",          // Область/регіон
    region: "Central Ukraine",   // Макрорегіон
    province: "Kyiv Province",   // Провінція
    county: "Kyiv District",     // Район
    
    // Населені пункти
    city: "Kyiv",               // Місто
    town: "Brovary",            // Містечко
    village: "Boryspil",        // Село
    municipality: "Kyiv City",  // Муніципалітет
    
    // Інше
    road: "Khreshchatyk Street",
    postcode: "01001",
    suburb: "Shevchenkivskyi"
  }
}
```

## Логіка вибору region

Код намагається знайти найбільш релевантне значення для `region`:

```javascript
this.region = address.state ||        // 1. Пріоритет: state (область)
             address.region ||        // 2. region (макрорегіон)
             address.province ||      // 3. province (провінція)
             address.county ||        // 4. county (район)
             address.city ||          // 5. city (місто)
             address.town ||          // 6. town (містечко)
             address.village ||       // 7. village (село)
             '';                      // 8. Пусто, якщо нічого не знайдено
```

## Візуальні індикатори

### 1. Loading Spinner
```vue
<span v-if="isGeocodingAddress">
  <span class="spinner-border spinner-border-sm"></span>
  <small>Finding location...</small>
</span>
```

### 2. Success Checkmark
```vue
<label>
  Country
  <small v-if="country" class="text-success">✓</small>
</label>
```

### 3. Info Text
```vue
<small v-if="country" class="text-muted">
  <i class="fas fa-info-circle"></i>
  Auto-filled from address
</small>
```

## Приклади використання

### Тест 1: Мінімальна адреса
```
Input: "Kyiv"
Output: 
  - country: "Ukraine"
  - region: "Kyiv City"
  - lat: 50.4501
  - lon: 30.5234
```

### Тест 2: Місто + країна
```
Input: "Lviv, Ukraine"
Output:
  - country: "Ukraine"
  - region: "Lviv Oblast"
  - lat: 49.8397
  - lon: 24.0297
```

### Тест 3: Повна адреса українською
```
Input: "вулиця Хрещатик 22, Київ, Україна"
Output:
  - country: "Ukraine"
  - region: "Kyiv City"
  - lat: ~50.447
  - lon: ~30.524
```

### Тест 4: Регіон
```
Input: "Dnipropetrovsk Oblast, Ukraine"
Output:
  - country: "Ukraine"
  - region: "Dnipropetrovsk Oblast"
  - lat: 48.4650
  - lon: 35.0462
```

## Console Logging

Код виводить інформацію в консоль для debugging:

```javascript
console.log('📍 Location found:', {
  country: 'Ukraine',
  region: 'Kyiv City',
  lat: 50.4501,
  lon: 30.5234,
  display_name: 'Kyiv, Ukraine'
});
```

**Приклад виводу:**
```
📍 Location found:
  country: "Ukraine"
  region: "Kyiv City"
  lat: 50.4501
  lon: 30.5234
  display_name: "Kyiv, Ukraine"
```

## Debouncing (затримка)

Щоб уникнути надмірної кількості запитів до API:

```javascript
handleAddressInput() {
  clearTimeout(this.addressInputTimeout);
  
  if (this.address.length > 5) {
    this.addressInputTimeout = setTimeout(() => {
      this.updateMapPreview();
    }, 1000); // Чекає 1 секунду
  }
}
```

**Як працює:**
1. Користувач вводить "K" → таймер запускається
2. Користувач вводить "y" → таймер скидається і запускається знову
3. Користувач вводить "i" → таймер скидається і запускається знову
4. Користувач вводить "v" → таймер скидається і запускається знову
5. Користувач зупиняється на 1 секунду → запит відправляється

## Error Handling

Якщо geocoding не вдається:

```javascript
catch (error) {
  console.log('Preview geocoding failed (not critical):', error);
  // Очистити поля
  this.country = '';
  this.region = '';
  this.latitude = null;
  this.longitude = null;
}
```

**Товар все одно буде створено**, просто:
- Без автозаповнення
- Користувач може ввести країну/регіон вручну
- Backend спробує зробити geocoding при створенні

## Rate Limiting

**Важливо:** Nominatim дозволяє **максимум 1 запит/секунду**.

Наш код дотримується цього обмеження через:
1. **Debounce 1 секунда** - запит не раніше ніж через 1 сек після введення
2. **Backend rate limiting** - 1 запит/сек в geocoding_service.py

## Тестування

### Відкрийте консоль браузера
```
F12 → Console
```

### Введіть адресу
```
"Kyiv, Ukraine"
```

### Перевірте вивід
```
📍 Location found: {country: "Ukraine", region: "Kyiv City", ...}
```

### Перевірте поля форми
- ✅ Country автоматично заповнено: "Ukraine"
- ✅ Region автоматично заповнено: "Kyiv City"
- ✅ Координати знайдено: 50.4501, 30.5234
- ✅ Маркер з'явився на карті

## API Endpoint

**Base URL:**
```
https://nominatim.openstreetmap.org/search
```

**Параметри:**
- `q` - адреса (URL encoded)
- `format=json` - формат відповіді
- `addressdetails=1` - включити деталі адреси
- `limit=1` - максимум 1 результат

**Headers:**
```
User-Agent: GrainTrade.info
```

**Повний приклад:**
```
GET https://nominatim.openstreetmap.org/search?q=Kyiv%2C%20Ukraine&format=json&addressdetails=1&limit=1
User-Agent: GrainTrade.info
```

## Переклади

Додайте до i18n файлів:

```json
{
  "create_form": {
    "geocoding": "Пошук місцезнаходження...",
    "auto_filled": "Автоматично заповнено з адреси",
    "location_found": "Місцезнаходження знайдено"
  }
}
```

## Troubleshooting

### Проблема: Країна не заповнюється
**Рішення:** Перевірте консоль, можливо адреса не знайдена

### Проблема: Region пустий
**Рішення:** Nominatim може не мати інформації про регіон для цієї адреси

### Проблема: Занадто багато запитів
**Рішення:** Збільшіть debounce timeout з 1000ms до 2000ms

### Проблема: CORS помилка
**Рішення:** Перевірте User-Agent header (обов'язковий!)

---

**Готово!** Тепер поля автоматично заповнюються з Nominatim! 🎉
