import csv
import os
import sys

def load_and_validate_config(file_path):
    # Проверка: существует ли вообще файл конфигурации
    if not os.path.exists(file_path):
        print(f"Критическая ошибка: Файл конфигурации '{file_path}' не найден!")
        sys.exit(1)

    config = {}
    
    # Читаем CSV файл
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:  # Пропускаем пустые строки
                    continue
                if len(row) != 2:
                    print(f"Ошибка в CSV: Строка {row} должна содержать ровно два значения (ключ,значение).")
                    sys.exit(1)
                config[row[0].strip()] = row[1].strip()
    except Exception as e:
        print(f"Критическая ошибка при чтении файла: {e}")
        sys.exit(1)

    # СПИСОК ПРОВЕРОК (ВАЛИДАЦИЯ ОШИБОК)
    
    # 1. Проверяем имя пакета
    if 'package_name' not in config or not config['package_name']:
        print("Ошибка валидации: Параметр 'package_name' отсутствует или пуст!")
        sys.exit(1)

    # 2. Проверяем режим работы репозитория
    if 'repo_mode' not in config or config['repo_mode'] not in ['online', 'local']:
        print("Ошибка валидации: 'repo_mode' должен быть строго 'online' или 'local'!")
        sys.exit(1)

    # 3. Проверяем путь/URL
    if 'repository_path' not in config or not config['repository_path']:
        print("Ошибка валидации: 'repository_path' не может быть пустым!")
        sys.exit(1)

    # 4. Проверяем имя файла картинки (должно заканчиваться на .png)
    if 'output_image' not in config or not config['output_image'].endswith('.png'):
        print("Ошибка валидации: 'output_image' должен иметь расширение .png!")
        sys.exit(1)

    # 5. Проверяем ASCII режим (должен быть true или false)
    if 'ascii_mode' not in config or config['ascii_mode'].lower() not in ['true', 'false']:
        print("Ошибка валидации: 'ascii_mode' должен быть 'true' или 'false'!")
        sys.exit(1)

    # 6. Проверяем максимальную глубину (должно быть целое число >= 0)
    if 'max_depth' not in config:
        print("Ошибка валидации: Параметр 'max_depth' отсутствует!")
        sys.exit(1)
    try:
        depth = int(config['max_depth'])
        if depth < 0:
            raise ValueError
    except ValueError:
        print("Ошибка валидации: 'max_depth' должно быть целым положительным числом!")
        sys.exit(1)

    # 7. Проверяем подстроку для фильтрации (может быть пустой, но ключ должен быть)
    if 'filter_substring' not in config:
        print("Ошибка валидации: Параметр 'filter_substring' отсутствует!")
        sys.exit(1)

    return config

def main():
    config_file = "config.csv"
    
    # Загружаем и проверяем
    config = load_and_validate_config(config_file)
    
    # Выводим результат (Требование №3 задания)
    print("Параметры конфигурации успешно проверены");
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
