#!/usr/bin/env python3
# coding: utf-8
""" Module for timestamps on screenshots checking.
Copyleft 2021-22 by Roman M. Yudichev (industrialSAST@ya.ru)

Usage:
    ScrTimeCheck.py -c | --check <docx-file-mask> <date>
    ScrTimeCheck.py -s | --save <docx-file>
    ScrTimeCheck.py -p | --parse <txt-dir>
    ScrTimeCheck.py -h | --help
    ScrTimeCheck.py -v | --version
    
Options:
    -c --check     Комплексная проверка файлов на наличие скриншотов с датами ранее указанной.
    -s --save      Разобрать файл документа, найти картинки, сохранить их в каталог.
    -p --parse     Искать в файлах с распознанным текстом все сигнатуры даты/времени.
    -h --help      Show this screen.
    -v --version   Show version.

    Примеры:
         ScrTimeCheck.py -c topdir/**/*.doc*  "2021-01-10" - найти рекурсивно в файлах doc* _всех_ подкаталогов
                каталога topdir любой степени вложенности (маска "**") скриншоты с датами ранее 10 января 2021 года.

"""
import glob
import datetime
import datetime_matcher
import docopt
from docx import Document
import os
from pathlib import Path
from PIL import Image
from termcolor import colored
import pytesseract


ScrTimeCheck_version = '2.0.2'

img_subdir_name = 'img'

# Вернуть имя с уникальным префиксом типа "(1)", если есть дубликат
def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 0

    while os.path.exists(path):
        if counter > 0:
            print("Output directory already exist: {}".format(path))
            path = "{}({}){}".format(filename, str(counter), extension)
        counter += 1

    return path

def create_work_dir(filename, date):
    p = uniquify(Path(os.getcwd()) / Path("{}_{}".format(filename, date)))
    os.makedirs(p)

    return p


def create_image_dir(work_dir):
    image_dir_name = Path(work_dir) / img_subdir_name

    print("image_dir_name = {}".format(image_dir_name))

    os.makedirs(image_dir_name)

    return image_dir_name


#
# Создать каталог для изображений.
# Сохранить в каталог все изображения, которые есть в файле документа
#
def save_images(filepath, dir):
    doc = Document(filepath)

    print("Writing images from {} document to separate files...".format(filepath))
    total = 0
    # Количество разрядов в индексе картинки
    num_lengh = len(str(len(doc.inline_shapes)))
    for count, s in enumerate(doc.inline_shapes):
        total = count
        content_id = s._inline.graphic.graphicData.pic.blipFill.blip.embed
        content_type = doc.part.related_parts[content_id].content_type
        if not content_type.startswith('image'):
            continue
        # Если имена изображений совпадают, дополнить имена файлов уникальными суффиксами.
        # Цифровые индексы картинок делать одинаковой длины, добивая лидирующими нулями до нужной.
        img_name = uniquify(Path("{}".format(dir)) / Path("{}_{}".format(str(count + 1).zfill(num_lengh),
            os.path.basename(doc.part.related_parts[content_id].partname))))
        img_data = doc.part.related_parts[content_id]._blob

        with open(img_name, 'wb') as fp:
            fp.write(img_data)
    print("{} images has been saved.".format(total+1))


# Грубая проверка на опечатки и ошибки распознавания
def sounds_reasonable(item):
    past = datetime.date(1970, 1, 1)
    future = datetime.date(2099, 12, 31)

    present = item.date()
    # Проверка на "до-Unix'овую эру" и на "будущее"
    return past < present < future


# Поиск таймстампов в строке
def find_timestamps(text, date):
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

    dtmatcher = datetime_matcher.DatetimeMatcher()
    search = r'%d(\/|\.|\\)%M(\/|\.|\\)%Y'

    dates = dtmatcher.extract_datetimes(search, text)
    results = []

    if dates:
        for item in dates:
            if sounds_reasonable(item):
                if item.date() < datetime.date.fromisoformat(date):
                    results.append(item)
    return results


#
# Создать каталог для распознаваемого языка текста.
# Распознать текст на заданном языке на изображениях и сохранить в файлы.
# dir_path - путь к каталогу с изображениями
# language - язык распознавания
#
def img2txt_on_lang(dir_path, text_dir_path, language):
    # Отобразить сообщение для пользователя
    print("Start text recognition on [{}] language...".format(language))
    print("dir_path = {}, text_dir_path = {}, language = {}".format(dir_path, text_dir_path, language))
    # Путь к каталогу с изображениями
    d_path = Path(dir_path)
    # Создать подкаталог для текстовых файлов на целевом языке
    # Имя подкаталога для текстов на текущем распознаваемом языке
    lang_dir = Path(text_dir_path) / Path("{}".format(language))
    # Если подкаталог ещё не существует - создать его
    if not os.path.exists(lang_dir):
        os.makedirs(lang_dir, exist_ok=True)

    # Перечислить все файлы изображений
    for img in [f for f in os.listdir(dir_path) if os.path.isfile(Path(dir_path) / Path(f))]:
        # TODO: Вставить прогрессбар
        # Собрать полный путь к файлу изображения
        img_name = d_path / img
        # Собрать полный путь к файлу с распозанным текстом
        txt_file_name = lang_dir / "{}.{}.txt".format(img, language)
        print(txt_file_name)
        # Если изображение ещё не распознано - запустить распознавание
        if not os.path.exists(txt_file_name) or os.stat(txt_file_name).st_size == 0:
            result = pytesseract.image_to_string(Image.open(img_name), lang=language)
            if result:
                with open(txt_file_name, 'w', encoding='utf-8') as fp:
                    fp.write(result)
        else:
            continue
    return lang_dir


# dir_path - путь к каталогу с изображениями
def img2txt(img_dir_path, text_dir_path):
    return img2txt_on_lang(img_dir_path, text_dir_path, 'eng'), img2txt_on_lang(img_dir_path, text_dir_path, 'rus')


# Печать найденного текста с подсветкой найденных таймстампов
def print_w_highlight(text, date):
    for s in text.split('\n'):
        if find_timestamps(s, date):
            print(colored(s, 'red'))
        else:
            print(colored(s, 'green'))
    return


# Для каждого текстового файла в указанном каталоге
# распознать дату в каждой строке
def process_txt_dir(txtdir, date):
    print("Starting text files processing...")
    for txt_file in [f for f in os.listdir(txtdir) if os.path.isfile(Path(txtdir) / Path(f))]:
        with open(Path(txtdir) / Path(txt_file), 'r', encoding='utf-8') as fp:
            text = fp.read()
            results = find_timestamps(text, date)
            if results:
                print(
                    "Found in {}:".format(txt_file))
                for item in results:
                    print(item.strftime('%d/%m/%Y'))


# Вывести задание на экран
def show_task(f_mask, date):
    print("Task: to find the timestamps earlier than {} at the file(s) `{}`.\n".format(date, f_mask))
    count_files = 0
    for file in glob.iglob(f_mask, recursive=True):
        if os.path.isfile(file):
            count_files +=1
    if count_files == 0:
        print("There are no files found.\nExit whithout any work done.")
        exit(1)
    else:
        if count_files == 1:
            print("There is one file found.")
        else:
            print("There are {} files found.".format(count_files))

# Проверить file на наличие на скриншотах дат не позже date
def check_files(file_mask, date):
    show_task(file_mask, date)

    # Найти все файлы, удовлетворяющие маске
    for file in glob.iglob(file_mask, recursive=True):
        if os.path.isfile(file):
            print("Processing file {}...\n".format(file))
            # Создать рабочий каталог
            work_dir = create_work_dir(os.path.basename(file)[:-5], date)
            # Создать каталог для изображений
            image_dir_name = create_image_dir(work_dir)
            # Создать каталог для текстов
            txt_dir = Path(work_dir) / Path("text")
            if not os.path.exists(txt_dir):
                os.makedirs(txt_dir)
            # 2 Сохранить картинки в каталог
            save_images(file, image_dir_name)

            # 3 Получить текст из картинок
            if os.path.exists(image_dir_name):
                txt_eng_dir, txt_rus_dir = img2txt(image_dir_name, txt_dir)

                # 4 Обработать текст и найти вхождения дат
                if os.path.exists(txt_eng_dir):
                    print("English text...")
                    process_txt_dir(txt_eng_dir, date)
                if os.path.exists(txt_rus_dir):
                    print("Russian text...")
                    process_txt_dir(txt_rus_dir, date)


def check_arguments(args):
    if args["--save"]:
        if args["<docx-file>"]:
            if os.path.exists(args["<docx-file>"]):
                save_images(args["<docx-file>"], args["<date>"])
            else:
                print("File {} does not exist. Could you check file path, pls?")
        else:
            print("Please point docx file.")
    elif args["--parse"]:
        if args["<txt-dir>"]:
            if os.path.exists(args["<txt-dir>"]):
                process_txt_dir(args["<txt-dir>"], args["<date>"])
            else:
                print("Directory {} with texts is not exist...".format(args["<txt-dir>"]))
        else:
            print("Please point directory to store txt files.")
    elif args["--check"] and args["<docx-file-mask>"] and args["<date>"]:
        if args["<date>"]:
            check_files(args["<docx-file-mask>"], args["<date>"])
        else:
            print('Please point the deadline date ("YYYY-MM-DD").')
    else:
        print("Please point all the arguments correctly.")
        print(args)


###############################################################################
if __name__ == "__main__":
    try:
        arguments = docopt.docopt(__doc__, version='ScrTimeCheck ' + ScrTimeCheck_version)
        check_arguments(arguments)
    except docopt.DocoptExit as e:
        print(e)
