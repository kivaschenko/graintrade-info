import requests
from bs4 import BeautifulSoup
import pandas as pd

def parse_tripoli_nibulon(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # На сайті зазвичай кілька таблиць (Порти та Елеватори)
        tables = soup.find_all('table')
        
        all_data = []

        for table in tables:
            # Отримуємо заголовки (культури: Пшениця, Кукурудза тощо)
            headers_row = table.find('tr')
            if not headers_row:
                continue
                
            columns = [th.text.strip() for th in headers_row.find_all(['th', 'td'])]
            
            # Обробляємо рядки з даними
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue
                
                # Структура рядка: 0 - Назва, 1 - Адреса (Регіон), інші - ціни
                entry = {
                    "Підприємство": cells[0].text.strip(),
                    "Адреса/Регіон": cells[1].text.strip().replace('\n', ' ')
                }
                
                # Додаємо ціни відповідно до заголовків колонок
                for i in range(2, len(cells)):
                    if i < len(columns):
                        culture_name = columns[i]
                        price_value = cells[i].text.strip()
                        entry[culture_name] = price_value
                
                all_data.append(entry)

        # Створюємо таблицю
        df = pd.DataFrame(all_data)
        
        # Очистка: видаляємо порожні символи та '-'
        df = df.replace('-', '')
        
        return df

    except Exception as e:
        print(f"Помилка при парсингу: {e}")
        return None

# Використання
url = "https://tripoli.land/ua/nibulon"
data = parse_tripoli_nibulon(url)

if data is not None:
    # Вивести перші 10 записів
    print(data.head(10))
    
    # Зберегти в Excel (зручніше для цін) або CSV
    data.to_csv("nibulon_prices.csv", index=False)
    print("\nДані успішно збережено у файл nibulon_prices.csv")