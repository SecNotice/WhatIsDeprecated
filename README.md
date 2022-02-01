# WhatIsDeprecated
Screenshot recognition, information extraction to find obsolete artifacts.

Проверка скриншотов на наличие таймстампов.

## Зависимости

Python >= 3.8.

### Tesseract:
**Windows:**  https://github.com/UB-Mannheim/tesseract/wiki

В ходе инсталляции нужно выбрать языки, для которых будут установлены тренировочные данные (как минимум - Russian, Englis).

**Linux:** 

`sudo apt install tesseract-ocr -y`
`sudo apt install tesseract-ocr-rus -y`

На Astra Linux Orel (2.12.43)  - установить curl, а затем pip3:

`sudo apt install curl`

`curl -sS https://bootstrap.pypa.io/pip/3.5/get-pip.py | sudo python3`

`ln /usr/local/bin/pip3 /usr/bin/pip3`


## Установка 
1. Установить пакеты из requirements.txt:

`pip install -r ./requirements.txt`


## Использование

    `ScrTimeCheck.py -c ./report.docx  "2021-01-10"`
    `ScrTimeCheck.py -c topdir/**/*.doc*  "2021-01-10"`