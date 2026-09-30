# практика 

## задание 1
```
localhost:~# cd /etc
localhost:/etc#  ls

localhost:/etc# cut -d: -f1 passwd | sort
```
## задание 2
```
localhost:/etc# awk '{print $2, $1} ' protocols | sort -nr | head -n 5
```
## задание 3
```
text="$1"
length=${#text}
border=""

for ((i=0; i<length; i++)) do
    border="${border}-"
done

echo "+${border}+"
echo "|${text}|"
echo "+${border}+"
```
## задание 4
```
if [ -z "$1" ]; then
        echo "Использование: $0 <имя_файла>"
        exit
fi
 
filename="$1"
 
if [ ! -f "$filename" ]; then
        echo "Ошибка: файл $filename не найден."
        exit 1
fi
 
grep -oE '[a-zA-Z_][a-zA-Z0-9_]*' "$filename" | sort -u | tr '\n' ' '
echo ""
```
## задание 5
```
file_to_reg="$1"
 
chmod +x "$file_to_reg"
 
cp "$file_to_reg" /usr/local/bin/
```
## задание 6
```
for f in *; do
    [[ "$f" =~ \.py$ ]] && head -n 1 "$f" | grep -q "^#" && echo "$f: Есть"
    [[ "$f" =~ \.(c|js)$ ]] && head -n 1 "$f" | grep -q -E "^(//|/\*)" && echo "$f: Есть"
done
```
## задание 7
```
if [ -z "$1" ]; then
    echo "Надо указать папку! Пример: $0 /home/user"
    exit 1
fi

# Находим файлы, считаем их хеши, сортируем и выводим только повторы
find "$1" -type f -exec md5sum {} + | sort | uniq -w 32 -d --all-repeated=separate
```
## задание 8
```
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Мало аргументов! Надо так: $0 <расширение> <имя_архива.tar>"
    exit 1
fi

# Ищем файлы с этим расширением и пихаем в tar
find . -maxdepth 1 -type f -name "*.$1" | tar -cvf "$2" -T -
```
## задание 9
```
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Забыл файлы указать! Надо: $0 <старый_файл> <новый_файл>"
    exit 1
fi

# Утилита sed на лету меняет 4 пробела на \t
sed 's/    /\t/g' "$1" > "$2"
echo "Готово! Исправленный файл лежит в $2"
```
## задание 10
```
if [ -z "$1" ]; then
    echo "Папку укажи! Пример: $0 /var/log"
    exit 1
fi

# Ищем файлы *.txt с размером (size) ровно 0 байт
find "$1" -maxdepth 1 -type f -name "*.txt" -size 0 -exec basename {} \;
```
