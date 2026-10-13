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
                if not row or len(row) < 2: 
                    continue
                # Извлекаем ключ и значение из списка row
                key = row[0].strip()
                value = row[1].strip()
                config[key] = value
    except Exception as e:
        print(f"Критическая ошибка при чтении файла: {e}")
        sys.exit(1)
    return config
def get_direct_deps(repo_path, repo_mode, target_package):
    dependencies = []
    
    # Пункт 5: чтение из локального текстового файла
    if repo_mode == 'local':
        if not os.path.exists(repo_path):
            print(f"Ошибка: Тестовый файл репозитория '{repo_path}' не найден.")
            return []
        with open(repo_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip() or ':' not in line: continue
                pkg, deps_str = line.split(':', 1)
                if pkg.strip() == target_package:
                    return deps_str.strip().split()
        return []

    # Режим ОНЛАЙН (из ЭТАПА 2 с Яндексом)
    else:
        index_url = "https://yandex.ru" if repo_path == 'yandex' else repo_path.rstrip('/') + '/APKINDEX.tar.gz'
        try:
            req = urllib.request.Request(index_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                compressed_data = response.read()
            with tarfile.open(fileobj=io.BytesIO(compressed_data), mode="r:gz") as tar:
                content = tar.extractfile("APKINDEX").read().decode('utf-8')
                for pkg in content.split('\n\n'):
                    lines = pkg.split('\n')
                    pkg_name, pkg_deps = "", []
                    for line in lines:
                        if line.startswith('P:'): pkg_name = line[2:]
                        elif line.startswith('D:'): pkg_deps = line[2:].split()
                    if pkg_name == target_package:
                        for dep in pkg_deps:
                            clean = dep.replace('=', ' ').replace('<', ' ').replace('>', ' ').replace('!', ' ').split()
                            if not clean.startswith('so:') and not clean.startswith('cmd:'):
                                dependencies.append(clean)
                        break
        except Exception:
            return []
    return dependencies

# этап 3: Построение графа алгоритмом DFS БЕЗ рекурсии 
def build_dependency_graph(root_package, repo_path, repo_mode, max_depth, filter_sub):
    graph = {}  # Итоговый граф: {пакет: [список зависимостей]}
    
    # Стек для DFS хранит кортежи: (текущий_пакет, текущая_глубина)
    stack = [(root_package, 0)]
    visited = set() # Чтобы не зацикливаться (Пункт 4)

    while stack:
        current_pkg, current_depth = stack.pop() # Достаем элемент из конца (LIFO)
        
        # Проверка фильтрации (Пункт 3): если имя содержит подстроку, пропускаем его
        if filter_sub and filter_sub in current_pkg:
            continue
            
        # Проверка максимальной глубины (Пункт 2)
        if current_depth >= max_depth:
            continue

        if current_pkg in visited:
            continue
        visited.add(current_pkg)

        # Получаем прямые зависимости пакета (ЭТАП 2)
        deps = get_direct_deps(repo_path, repo_mode, current_pkg)
        
        # Фильтруем зависимости перед добавлением
        valid_deps = []
        for dep in deps:
            if filter_sub and filter_sub in dep:
                continue # Пропускаем отфильтрованные пакеты
            valid_deps.append(dep)
            
            # Если зависимость еще не обрабатывали, кидаем в стек и увеличиваем глубину на 1
            if dep not in visited:
                stack.append((dep, current_depth + 1))
        
        graph[current_pkg] = valid_deps

    return graph

def main():
    config = load_and_validate_config("config.csv")
    
    package = config.get('package_name')
    repo_path = config.get('repository_path')
    repo_mode = config.get('repo_mode', 'local')
    max_depth = int(config.get('max_depth', 3))
    filter_sub = config.get('filter_substring', '')

    print(f" Этап 3 (Режим: {repo_mode.upper()}) ")
    print(f"Анализ пакета: {package} | Глубина: {max_depth} | Фильтр: '{filter_sub}'")
    
    # Строим транзитивный граф без рекурсии (Пункт 1)
    graph = build_dependency_graph(package, repo_path, repo_mode, max_depth, filter_sub)
    
    print("\nПостроенный граф зависимостей:")
    for node, edges in graph.items():
        print(f"  {node} -> {edges if edges else '[]'}")
        
if __name__ == "__main__":
    main()
