import csv
import os
import sys
import urllib.request
import gzip
import tarfile
import io

def load_and_validate_config(file_path):
    if not os.path.exists(file_path):
        print(f"Критическая ошибка: Файл конфигурации '{file_path}' не найден!")
        sys.exit(1)
    config = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row: continue
                config[row[0].strip()] = row[1].strip()
    except Exception as e:
        print(f"Критическая ошибка при чтении файла: {e}")
        sys.exit(1)
    return config

def get_apk_dependencies(repo_url, target_package):
    # Формируем полный URL к индексу пакетов Alpine
    index_url = repo_url.rstrip('/') + '/APKINDEX.tar.gz'
    print(f"Скачиваем индекс репозитория: {index_url}...")
    
    try:
        # Скачиваем APKINDEX в память
        req = urllib.request.Request(index_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            compressed_data = response.read()
    except Exception as e:
        print(f"Ошибка при скачивании репозитория: {e}")
        sys.exit(1)

    print("Распаковываем индекс пакетов...")
    dependencies = []
    
    try:
        # Распаковываем tar.gz в памяти
        with tarfile.open(fileobj=io.BytesIO(compressed_data), mode="r:gz") as tar:
            # Находим внутри архива файл APKINDEX
            apkindex_file = tar.extractfile("APKINDEX")
            if apkindex_file is None:
                print("Ошибка: Файл APKINDEX не найден внутри архива.")
                sys.exit(1)
                
            # Читаем текст индекса
            content = apkindex_file.read().decode('utf-8')
            
            # Разделяем файл на блоки (каждый пакет разделен двумя переносами строк)
            packages = content.split('\n\n')
            
            current_package_deps = None
            package_found = False

            for pkg in packages:
                lines = pkg.split('\n')
                pkg_info = {}
                for line in lines:
                    if line.startswith('P:'): # Имя пакета
                        pkg_info['name'] = line[2:]
                    elif line.startswith('D:'): # Зависимости пакета
                        pkg_info['deps'] = line[2:].split()

                # Если нашли наш пакет, вытаскиваем его зависимости
                if pkg_info.get('name') == target_package:
                    package_found = True
                    raw_deps = pkg_info.get('deps', [])
                    # Очищаем зависимости от версий (например, состригаем 'so:libc.musl-x86_64.so.1' или '>3.0')
                    for dep in raw_deps:
                        # Убираем спецсимволы и проверки версий
                        clean_dep = dep.split('<')[0].split('>')[0].split('=')[0].split('!')[0]
                        if clean_dep and not clean_dep.startswith('so:'): # Игнорируем системные .so библиотеки
                            dependencies.append(clean_dep)
                    break
            
            if not package_found:
                print(f"Предупреждение: Пакет '{target_package}' не найден в этом репозитории.")

    except Exception as e:
        print(f"Ошибка при обработке APKINDEX: {e}")
        sys.exit(1)

    return dependencies

def main():
    config_file = "config.csv"
    config = load_and_validate_config(config_file)
    
    package = config.get('package_name')
    repo_url = config.get('repository_path')
    
    print(f"Анализируем пакет: {package}")
    
    # Получаем прямые зависимости (Требование №2)
    deps = get_apk_dependencies(repo_url, package)
    
    # Выводим результат на экран (Требование №3)
    print(f"\n=== Прямые зависимости пакета '{package}' ===")
    if deps:
        for dep in deps:
            print(f" - {dep}")
    else:
        print(" У этого пакета нет прямых зависимостей (или они являются системными библиотеками).")

if __name__ == "__main__":
    main()
