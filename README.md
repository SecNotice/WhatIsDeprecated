# WhatIsDeprecated
Screenshot recognition, information extraction to find obsolete artifacts.

Проверка скриншотов на наличие таймстампов.

## Зависимости

Python >= 3.8.

На Astra Linux Orel (2.12.43)  - установить curl, а затем pip3:

`sudo apt install curl`

`curl -sS https://bootstrap.pypa.io/pip/3.5/get-pip.py | sudo python3`

`ln /usr/local/bin/pip3 /usr/bin/pip3`


## Установка 
1. Установить пакеты из requirements.txt:

`pip install -r ./requirements.txt`

2. Скопировать rus.traineddata в каталог:

**Windows:** `c:\Users\<user_name>\AppData\Local\Programs\Python\<версия python>\Lib\site-packages\TextExtractApi\tessdata\` 

**Linux:** `/usr/local/share/tessdata/`

`sudo mv -v rus.traineddata /usr/local/share/tessdata/`

## Использование

