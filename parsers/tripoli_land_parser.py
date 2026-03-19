from pathlib import Path
from datetime import datetime, timezone
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://tripoli.land"

COMPANIES = {
    "nibulon": "Нібулон",
    "kernel": "Кернел",
    "lnz-group": "ЛНЗ Груп",
    "tas-agro": "ТАС АГРО",
    "astarta-kiev": "Астарта-Київ",
    "mhp": "МХП",
    "agroprosperis": "Агропросперіс (NCH)"
    # Додайте інші компанії за потреби
}
BASE_OUT_DIR = Path(__file__).resolve().parent.parent.parent
RESULT_DIR = BASE_OUT_DIR / "parsers_results" / "tripoli_land"
os.makedirs(RESULT_DIR, exist_ok=True)
TIMESTAMP = ' '.join(datetime.now(timezone.utc).isoformat().split('.')[0].split('T'))
FILENAME_RESULT = f"{RESULT_DIR}/tripoli_prices_{TIMESTAMP.replace(':', '-').replace(' ', '_')}.csv"

def parse_company_prices(company_slug: str, company_name: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    # Формуємо URL для компанії
    url = BASE_URL + f"/ua/companies/{company_slug}"

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

            # Перевіряємо тип зберігання за заголовком таблиці
            storage_type = headers_row.th.text.strip() if headers_row and headers_row.th else '' # Порт або Елеватор

            if not storage_type or storage_type not in ['Порт', 'Елеватор']:
                continue

            columns = [th.text.strip() for th in headers_row.find_all(['th', 'td'])[1:]]  # Пропускаємо першу колонку (Назва/Адреса)
            
            # Обробляємо рядки з даними
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue
                
                # First column is combined name/address, others are prices
                location_info = cells[0]
                storage_name = location_info.b.text.strip() if location_info.b else ''
                region = location_info.p.text.strip() if location_info.p else ''
                entry = {
                    "Час збору": TIMESTAMP,
                    "Компанія": company_name,
                    "Тип зберігання": storage_type,
                    "Місце зберігання": storage_name,
                    "Адреса/Регіон": region
                }
                
                # Додаємо ціни відповідно до заголовків колонок
                for i in range(1, len(cells)):
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


def main():
    """Головна функція для парсингу цін Tripoli Land та збереження у файл"""
    data = pd.DataFrame()
    # Execution
    for company_slug, company_name in COMPANIES.items():
        print(f"Парсинг цін для компанії: {company_name} ({company_slug})")
        data_company = parse_company_prices(company_slug, company_name)
        if data_company is not None:
            print(f"Знайдено записів: {len(data_company)}")
            print(data_company.head(3))
            data = pd.concat([data, data_company], ignore_index=True)
        else:
            print(f"Не вдалося отримати дані для компанії: {company_name}")

    if data is not None:
        # Вивести перші 10 записів
        print(data.head(10))
        
        # Зберегти в Excel (зручніше для цін) або CSV
        data.to_csv(FILENAME_RESULT, index=False)
        print(f"\nДані успішно збережено у файл {FILENAME_RESULT}")

if __name__ == "__main__":
    main()
    # Для тестування парсингу однієї компанії
    # test_company_slug = "kernel"
    # test_company_name = "Кернел"
    # df_test = parse_company_prices(test_company_slug, test_company_name)
    # if df_test is not None:
    #     print(df_test.head(10))