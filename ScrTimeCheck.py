#!/usr/bin/env python3
# coding: utf-8
""" Module for timestamps on screenshots checking.
Copyleft 2021 by Roman M. Iudichev (industrialsast@ya.ru)

Usage:
    ScrTimeCheck.py -s | --save <docx-file>
    ScrTimeCheck.py -g | --get-text <img-dir>
    ScrTimeCheck.py -p | --parse <txt-dir>
    ScrTimeCheck.py -c | --check <docx-file> <date>
    ScrTimeCheck.py -h | --help
    ScrTimeCheck.py -v | --version
    
Options:
    -s --save      Разобрать файл документа, найти картинки, сохранить их в каталог.
    -g --get-text  Выделить из картинок в каталоге текст (eng, rus) и сохранить в файлы саммари "*.eng.txt" и "*.rus.txt".
    -p --parse     Искать в текстовых саммари сигнатуры даты\времени.
    -c --check     Комплексная проверка файла на наличие скриншотов с датами ранее указанной (заготовка на будущее, пока не работает).
    -h --help      Show this screen.
    -v --version   Show version.
"""

import colorama
import datetime
from datetime_matcher import DatetimeMatcher
import docopt
from docx import Document
import os
from os import listdir
from os.path import isfile, join
from PIL import Image
from termcolor import colored
from TextExtractApi.TextExtract import TextExtractFunctions

# TODO: Проверить - работает ли настройка?
Image.MAX_IMAGE_PIXELS = None

ScrTimeCheck_version='1.1'

def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 0

    while os.path.exists(path):
        print("   exist: ", path)
        if counter > 0:
            path = filename + "(" + str(counter) + ")" + extension
        counter += 1

    return path

def create_image_dir(filename):
    image_dir_name = uniquify(os.getcwd() + '\\' + filename)

    print("image_dir_name = ", image_dir_name)
    os.mkdir(image_dir_name)
    
    return image_dir_name

#
# Создать каталог для изображений.
# Сохранить в каталог все изображения, которые есть в файле документа
#
def save_images(filepath):
    doc = Document(filepath)
    image_dir_name = create_image_dir(os.path.basename(filepath)[:-5])
    
    # Количество разрядов в индексе картинки
    num_lengh = len(str(len(doc.inline_shapes)))
    for count, s in enumerate(doc.inline_shapes):
        contentID = s._inline.graphic.graphicData.pic.blipFill.blip.embed
        contentType = doc.part.related_parts[contentID].content_type
        if not contentType.startswith('image'):
            continue
        # Если имена изображений совпадают, дополнить имена файлов уникальными суффиксами.
        # Цифровые индексы картинок делать одинаковой длины, добивая лидирующими нулями до нужной.
        imgName = uniquify("{}\\".format(image_dir_name) + str(count+1).zfill(num_lengh) + '_' + os.path.basename(doc.part.related_parts[contentID].partname))
        imgData = doc.part.related_parts[contentID]._blob
        
        with open(imgName, 'wb') as fp:
            print("Writing {} ...".format(imgName))
            fp.write(imgData)
    return

# Грубая проверка на опечатки и ошибки распознавания
def sounds_reasonable(item):
    past = datetime.date(1970, 1, 1)
    future = datetime.date(2099, 12, 31)
    
    present = item.date()
    return (
        # Проверка на "до-Unix'овую эру"
        past < present and
        # Проверка на "будущее"
        present < future
    )

# Поиск таймстампов в строке
def find_timestamps(text):
    print(text)
    # Примеры строк с датами:
    #
    # Thu, 01-Jan-197 0 00:00:01 GMT
    # Jan 16 '16 at 13:33
    # fo 10.57 11/01/2021 Button DS1996 DI iButton DS1996 DI Bxoa agMuHuCcTpaTopa Yenex
    # 10.53 11/01/2021 iButton DS1996 DI (Button DS1996 DI Bxoa agmuHwcTpaTopa Yenex
    # 10.50 11/01/2021 iButton DS1996 DI (Button DS1996 DI Bxoa agmuHwcTpaTopa Yenex
    # 11:32 11/01/2021 iButton DS1996 DI (Button DS1996 DI Bxoa agmuHwcTpaTopa Yenex
    # Cm 11.23 11/01/2021 iButton DS1996 DI (Button DS1996 DI Bxoa agmuHwcTpaTopa Yenex
    # 1199 11/01/2021 iButton DS1996 DI (Button DS1996 DI Bxoa agmuHwcTpaTopa Yenex
    # 1198 11/01/2021 user! Button DS1994 3 MNonk308aTens cventn ceolinapont Yenex

    dtmatcher = DatetimeMatcher()
    # layout = search = r'%d\/%m\/%Y'
    layout = search = r'%d\/%M\/%Y'
    
    dates = dtmatcher.extract_datetimes(search, text)
    results = []

    if dates:
        for item in dates:
            if (sounds_reasonable(item)):
                results.append(item)
    else:
        print("-")
    return results

#
# Создать каталог для распознаваемого языка текста.
# Распознать текст на заданном языке на изображениях и сохранить в файлы.
#
def img2txt_on_lang(dir_path, language):
    if not os.path.exists(dir_path+'\\{}\\'.format(language)):
        os.mkdir(dir_path+'\\{}\\'.format(language))

    for img in [f for f in listdir(dir_path) if isfile(join(dir_path, f))]:
        imgName = dir_path + '\\'+img
        txtFileName = dir_path+'\\{}\\'.format(language) + img + '.{}.txt'.format(language)
        if not os.path.exists(txtFileName) or os.stat(txtFileName).st_size == 0:
            result,scale=TextExtractFunctions.image_to_string_only_nopreprocess(imgName, lang=language)
            if result:
                print("=== Image file: {} ===".format(imgName))
                print("\n\t", "=" * 10,"  Text in", colored("{}: ".format(language), 'green'), "=" * 10, "\n")
                print_w_highlight(result)

                with open(txtFileName, 'w', encoding='utf-8') as fp:
                    print("Writing {} ...\n".format(txtFileName))
                    fp.write(result)
        else:
            continue

def img2txt(dir_path):
    img2txt_on_lang(dir_path, 'eng')
    img2txt_on_lang(dir_path, 'rus')

# Печать найденного текста с подсветкой найденных таймстампов
def print_w_highlight(text):
    for s in text.split('\n'):
        if find_timestamps(s):
            print (colored(s, 'red'))
        else:
            print (colored(s, 'green'))
    return


# Для каждого текстового файла в указанном каталоге
# распознать дату в каждой строке
def process_txt_dir(dir):
    for txt_file in [f for f in listdir(dir) if isfile(join(dir, f))]:
        with open(join(dir, txt_file), 'r', encoding='utf-8') as fp:
            text = fp.read()
            results = find_timestamps(text)
            if results:
                print("В файле {} найдены даты:".format(txt_file))
                for item in results:
                    print(item.strftime('%d/%m/%Y'))

# Проверить file на наличие на скриншотах дат не позже date
def check_file(file, date):
    print("check_file")


def check_arguments(arguments):
    if arguments["--save"]:
        if arguments["<docx-file>"]:
            if os.path.exists(arguments["<docx-file>"]):
                save_images(arguments["<docx-file>"])
            else:
                print("File {} does not exist. Could you check file path, pls?")
        else:
            print("Please point docx file.")
    elif arguments["--get-text"]:
        if arguments["<img-dir>"]:
            if os.path.exists(arguments["<img-dir>"]):
                img2txt(arguments["<img-dir>"])
            else:
                print("Directory {} with texts does not exist...".format(arguments["<img-dir>"]))
        else:
            print("Please point image directory to text recognize.")
    elif  arguments["--parse"]:
        if  arguments["<txt-dir>"]:
            if os.path.exists(arguments["<txt-dir>"]) :
                process_txt_dir(arguments["<txt-dir>"])
            else:
                print("Directory {} with texts does not exist...".format(arguments["<txt-dir>"]))
        else:
            print("Please point directory to store txt files.")
    elif arguments["--check"] and arguments["<docx-file>"] and arguments["<date>"]:
        if os.path.exists(arguments["<docx-file>"]):
            if arguments["<date>"]:
                check_file(arguments["<docx-file>"], arguments["<date>"])
            else:
                print("Please point the deadline date.")
        else:
            print("File {} does not exist. Could you check file path, pls?")


            
###############################################################################
if __name__ == "__main__":
    colorama.init()
    try:
        arguments = docopt.docopt(__doc__, version = 'ScrTimeCheck ' + ScrTimeCheck_version)
        print (arguments)
        check_arguments(arguments)
    except (docopt.DocoptExit) as e:
        print (e)
