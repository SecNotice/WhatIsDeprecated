# WhatIsDeprecated
Screenshot recognition, information extraction to find obsolete artifacts.

Проверка скриншотов на наличие дат.

Скрипт ScrTimeCheck.py находит и выводит на экран все найденные даты ранее указанной при запуске. 
Даты распознаются со всех скриншотов \(и других изображений\), которые содержатся в обрабатываемом файле формата doc\\docx. Поддерживаются простые маски файлов \("*"\), поэтому множественная обработка файлов тоже возможна.

Для работы скрипту необходим установленный в системе пакет Tesseract-OCR (согласно его инструкции по установке, правильной установкой считается такая, когда вызов утилиты tesseract возможен без указания полного пути к ней).

## Зависимости

Для работы скрипту необходим установленный в системе интерпретатор Python версии равной или выше 3.8.

### Tesseract:
**Windows:**  https://github.com/UB-Mannheim/tesseract/wiki

В ходе инсталляции нужно выбрать языки, для которых будут установлены тренировочные данные (как минимум - Russian, Englis).

**Linux:** 

`sudo apt install tesseract-ocr -y`
`sudo apt install tesseract-ocr-rus -y`

На Astra Linux Orel (2.12.43) для корректной работы утилиты pip для установки Python-модулей необходимо установить curl, а затем pip3:

`sudo apt install curl`

`curl -sS https://bootstrap.pypa.io/pip/3.5/get-pip.py | sudo python3`

`ln /usr/local/bin/pip3 /usr/bin/pip3`


## Установка 

0. Установить git.

1. Установить Python 3.

2. Установить Tesseract-OCR.

3. Клонировать этот репозиторий.

4. Установить пакеты из requirements.txt:

`pip3 install -r ./requirements.txt`

или на Windows

`py -3 -m pip install -r requirements.txt`


## Использование

Для выполнения скрипта его с необходимыми параметрами нужно запустить с помощью интерпретатора **python3** (если он единственный в системе - может называться просто `python`). 

Чтобы не получать ошибок об отсутствующем файле `python` или `python3` и не указывать полный путь к интерпретатору Python, убедитесь, что путь к нему указан в системной переменной PATH.

    `python3 ./ScrTimeCheck.py -c ./report.docx  "2021-01-10"`
    `python3 ./ScrTimeCheck.py -c topdir/**/*.doc*  "2021-01-10"`

Под Windows используйте команду `py -3`:

    `py -3 ./ScrTimeCheck.py -c ./report.docx  "2021-01-10"`
    `py -3 ./ScrTimeCheck.py -c topdir/**/*.doc*  "2021-01-10"`




По результатам работы в текущем каталоге будет создан каталог (каталоги, если обрабатываемых файлов несколько) с именем обрабатываемого файла и указанной даты (например "report.docx_2021-01-10").

Если каталог с таким именем уже существует, будет создан новый каталог с таким же именем, но к которому будет добавлен суффикс типа "(1)", "(2)" и т.д. Это может быть полезно, если в разных обрабатываемых подкаталогах обнаружатся одноимённые файлы.

Скрип в ходе работы выводит на экран: имена обрабатываемых файлов, количество и названия найденных в них файлов изображений, названия файлов, содержащих полный распознанный из изображений текст  и найденные в этих текстах даты. 

Полученные из изображений тексты могут использоваться и для других целей.