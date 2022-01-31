# WhatIsDeprecated
Screenshot recognition, information extraction to find obsolete artifacts.

Проверка скриншотов на наличие таймстампов.

## Зависимости
Python >= 3.7. 
На Astra Linux Orel (2.12.43)  - установить curl, а затем pip3 (`curl -sS https://bootstrap.pypa.io/pip/3.5/get-pip.py | sudo python3`; `ln /usr/local/bin/pip3 /usr/bin/pip3`).


## Установка 
1. Установить пакеты из requirements.txt:
`pip.exe install -r ./requirements.txt`
2. Скопировать rus.traineddata в каталог `c:\Users\<user_name>\AppData\Local\Programs\Python\<версия python>\Lib\site-packages\TextExtractApi\tessdata\` (Windows) или `___` ([Astra] Linux)

