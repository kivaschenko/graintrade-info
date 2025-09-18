from message_extractor import MessageExtractor
import json


def test_extractor():
    # Create sample messages
    sample_messages = [
        {
            "message": "Пшениця 3 клас, протеїн 12.5%, Одеська обл. 100 тонн, 8300 грн/т. Тел: +380932182822"
        },
        {
            "message": "Соняшник, чистий, сухий. Київська область. 50т по 12000 грн. Ф1 якість. 0631234567"
        },
        {
            "message": "Кукурудза 500 тонн, Харківська область. Вологість 14%, 7200 грн/т +380501234567"
        },
    ]

    # Save sample messages to file
    with open("results/Zernovaya_Birzha_messages.json", "w", encoding="utf-8") as f:
        json.dump(sample_messages, f, ensure_ascii=False, indent=2)

    # Process messages
    extractor = MessageExtractor()

    print("Processing sample messages:")
    for msg in sample_messages:
        result = extractor.extract_info(msg["message"])
        print("\nOriginal message:", msg["message"])
        print("Extracted info:")
        for key, value in result.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    test_extractor()
