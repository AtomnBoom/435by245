import sys
import io
import asyncio
import argparse

# 🛠️ ФИКСАЦИЯ КОДИРОВКИ: Насильно переводим потоки вывода Windows в UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.aegis.core.router import AdaptiveRouter

async def test_ai_pipeline():
    # 🛠️ ИСПРАВЛЕНО: Все эмодзи удалены, текст полностью безопасен для CP1251/UTF-8
    print("[A.E.G.I.S.] ИНИЦИАЛИЗАЦИЯ ЖИВОГО ТЕСТА ИИ-КОНТУРА...")
    
    # Инициализируем адаптивный роутер (передаем заглушку реестра)
    router = AdaptiveRouter(registry=None)
    
    print("\n--- ТЕСТ 1: ПРОВЕРКА ГЕНЕРАЦИИ ТЕКСТА (Динамический пул Ollama) ---")
    prompt = "Напиши одно короткое предложение: почему инженеры должны соблюдать ГОСТ?"
    print(f"Отправляю промпт: '{prompt}'")
    print("Роутер оценивает ОЗУ компьютера и выбирает оптимальную модель...")
    
    try:
        # Вызываем генерацию. Роутер сам выберет модель и автовыгрузит её из ОЗУ после ответа
        text_response = await router.generate(task_signature="complex_planning", prompt=prompt)
        print(f"\nОтвет Джарвиса:\n> {text_response}")
    except Exception as e:
        print(f"[Ошибка] Не удалось выполнить генерацию текста: {e}")
        print("Подсказка: Проверьте, запущен ли у вас сервис Ollama (ollama serve) и скачана ли хоть одна текстовая модель.")

    print("\n--- ТЕСТ 2: ПРОВЕРКА ВЕКТОРНОЙ ПАМЯТИ (Динамические Эмбеддинги) ---")
    test_text = ["Инженерный контур АЕГИС"]
    
    try:
        # Вызываем расчет векторов. Роутер сам найдет модель эмбеддингов
        vectors = await router.embed(texts=test_text)
        print(f"Успех! Получен вектор чисел.")
        print(f"Размерность вашего вектора: {len(vectors)} строк(и) чисел.")
    except Exception as e:
        print(f"[Ошибка] Не удалось сгенерировать векторы: {e}")
        print("Подсказка: Для прохождения этого теста скачайте модель эмбеддингов, например: ollama pull nomic-embed-text")

    print("\n[A.E.G.I.S.] ТЕСТ ИИ-КОНТУРА ЗАВЕРШЕН!")

if __name__ == "__main__":
    # Настраиваем чтение аргументов командной строки для будущей связки с Electron
    parser = argparse.ArgumentParser(description="A.E.G.I.S. Background Python Agent")
    parser.add_argument("--port", type=int, default=8190, help="Backend port")
    args = parser.parse_args()
    
    # Запускаем тестовый прогон ИИ-контура
    asyncio.run(test_ai_pipeline())
