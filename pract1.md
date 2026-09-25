# практика 

## задание 1
```
localhost:~# cd /etc
localhost:/etc#  ls

localhost:/etc# cut -d: -f1 passwd | sort
```
##задание 2
```
localhost:/etc# awk '{print $2, $1} ' protocols | sort -nr | head -n 5
```
##задание 3
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
##задание 4
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
##задание 5
```
file_to_reg="$1"
 
chmod +x "$file_to_reg"
 
cp "$file_to_reg" /usr/local/bin/
```
##задание 6
