# 🚀 Швидкий старт: Безкоштовний геокодинг

## Що змінилося?

**До**: Користувач шукав місце на карті Mapbox → дорого, повільно  
**Після**: Користувач вводить адресу → backend автоматично визначає координати → безкоштовно, швидко! ✅

## Приклади адрес, які працюють:

```
Київ
Одеса, Україна
вулиця Хрещатик, Київ
Lviv, Ukraine
Dnipro, Dnipropetrovsk Oblast, Ukraine
```

## Встановлення (5 хвилин)

### 1. Оновити базу даних

```bash
# Якщо база існує - виконати міграцію
docker exec -it graintrade-postgres psql -U your_user -d graintrade_db -f /docker-entrypoint-initdb.d/migration_add_address.sql

# АБО перестворити базу (видалить всі дані!)
docker-compose down -v postgres
docker-compose up -d postgres
```

### 2. Встановити залежності

```bash
cd backend
poetry add aiohttp
# або
pip install aiohttp
```

### 3. Перезапустити backend

```bash
docker-compose restart backend
```

### 4. Оновити frontend

```bash
cd frontend/src/components
cp ItemForm.vue ItemForm_old.vue  # backup
cp ItemForm_new.vue ItemForm.vue

cd ../..
npm run build
docker-compose restart frontend
```

## Використання в коді

### Frontend (ItemForm.vue)

```vue
<template>
  <div class="mb-3">
    <label>Адреса</label>
    <input v-model="address" placeholder="Київ, Україна" />
  </div>
  <div class="mb-3">
    <label>Країна</label>
    <input v-model="country" value="Ukraine" />
  </div>
</template>

<script>
export default {
  data() {
    return {
      address: '',
      country: 'Ukraine',
      latitude: null,  // Буде заповнено backend
      longitude: null  // Буде заповнено backend
    }
  },
  methods: {
    async createItem() {
      await axios.post('/items', {
        address: this.address,
        country: this.country,
        // координати визначаться автоматично
      })
    }
  }
}
</script>
```

### Backend (автоматично)

```python
# В item_routers.py вже реалізовано:
if item.latitude is None and item.address:
    lat, lon, country, region = await geocode_with_fallback(
        address=item.address,
        country=item.country
    )
    item.latitude = lat
    item.longitude = lon
```

## Тестування

```bash
# Перевірити geocoding сервіс
docker exec -it graintrade-backend python -c "
import asyncio
from app.service_layer.geocoding_service import geocode_address

async def test():
    result = await geocode_address('Київ, Україна')
    print(f'Координати Києва: {result}')

asyncio.run(test())
"
```

Очікуваний результат:
```python
{
    'latitude': 50.4501,
    'longitude': 30.5234,
    'country': 'Ukraine',
    'region': 'Kyiv City',
    'display_name': 'Kyiv, Ukraine'
}
```

## Переваги

| Показник | До | Після |
|----------|-----|-------|
| Вартість створення 1000 товарів | ~$5 | $0 ✅ |
| Швидкість створення | Повільно (карта) | Швидко (текст) |
| Ліміт на Free тарифі | 5 товарів | Можна збільшити до 50+ |
| Масовий імпорт | Дорого | Безкоштовно ✅ |

## Питання?

1. **Чи працює стара API з координатами?**  
   Так! Якщо передати `latitude` та `longitude` - geocoding не виконується.

2. **Що якщо адреса не знайдена?**  
   Товар створюється, але без координат (не відображається на карті).

3. **Чи потрібен Mapbox?**  
   Так, але тільки для відображення карти, не для geocoding.

4. **Скільки коштує Nominatim?**  
   Безкоштовно! Обмеження: 1 запит/сек (вже враховано в коді).

## Докладна документація

Див. `FREE_GEOCODING_IMPLEMENTATION.md` для повної інформації.

---

**Підсумок**: Створюйте необмежену кількість товарів безкоштовно! 🎉
