# WhatIsDeprecated
Screenshot recognition, information extraction to find obsolete artifacts.

Проверка скриншотов на наличие таймстампов

## Установка 

1. Установить Python 3.xx.xx. 
2. Установить зависимости:
c:\users\<username>\appdata\local\programs\python\<версия python>\python.exe  c:\users\<username>\appdata\local\programs\python\<версия python>\Scripts\pip.exe install -r ./requirements.txt
3. Скачать rus.traineddata из https://github.com/tesseract-ocr/tessdata/blob/master/rus.traineddata 
4. Скопировать rus.traineddata в каталог c:\Users\<user_name>\AppData\Local\Programs\Python\<версия python>\Lib\site-packages\TextExtractApi\tessdata\
5. Заменить файл TextExtract.py в каталоге c:\Users\<username>\AppData\Local\Programs\Python\<версия python>\Lib\site-packages\TextExtractApi\ на пропатченный.
