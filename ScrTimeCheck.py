#!/usr/bin/env python3
# coding: utf-8
""" Module for timestamps on screenshots checking.
Copyleft 2021-22 by Roman M. Yudichev (industrialSAST@ya.ru)

Usage:
    ScrTimeCheck.py -c | --check <docx-file-mask> <date>
    ScrTimeCheck.py -s | --save <docx-file>
    ScrTimeCheck.py -g | --get-text <img-dir>
    ScrTimeCheck.py -p | --parse <txt-dir>
    ScrTimeCheck.py -h | --help
    ScrTimeCheck.py -v | --version
    
Options:
    -c --check     Комплексная проверка файлов на наличие скриншотов с датами ранее указанной.
    -s --save      Разобрать файл документа, найти картинки, сохранить их в каталог.
    -g --get-text  Выделить из картинок в каталоге текст (eng, rus) и сохранить в файлы "*.eng.txt" и "*.rus.txt".
    -p --parse     Искать в файлах с распознанным текстом все сигнатуры даты/времени.
    -h --help      Show this screen.
    -v --version   Show version.

    Примеры:
         ScrTimeCheck.py -c topdir/**/*.doc*  "2021-01-10" - найти рекурсивно в файлах doc* _всех_ подкаталогов
                каталога topdir любой степени вложенности (маска "**") скриншоты с датами ранее 10 января 2021 года.

"""
import glob
import colorama
import datetime
import datetime_matcher
import docopt
from docx import Document
import os
from os import listdir
from os.path import isfile, join
from pathlib import Path
from PIL import Image
from termcolor import colored
from TextExtractApi.TextExtract import TextExtractFunctions
from TextExtractApi.TextExtract import TesseractOCR


# TODO: Fix error while russian text recognition.
# TODO: Increase CPU usage and total productivity and speed of work.

# TODO: Проверить - работает ли настройка?
Image.MAX_IMAGE_PIXELS = None

ScrTimeCheck_version = '1.2'


class WidExtractfunctions(TextExtractFunctions):
    def image_to_string_only(image_path, lang):
        """
            Extract result from image without matching expected text
        Args:
            image_path (str) : The path of image
            lang (str) : The Language of text
        Returns:
            (tuple): tuple containing:
                str : The result text of image (result)
                int : The scale of image (scale)
        """
        ocr_object = TesseractOCR(lang)
        result, na, scale = ocr_object.image_to_string(image_path, pre_process_img=False)
        return result, scale


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 0

    while os.path.exists(path):
        if counter > 0:
            print("Output directory already exist: {}".format(path))
            path = "{}({}){}".format(filename, str(counter), extension)
        counter += 1

    return path


def create_image_dir(filename, date):
    image_dir_name = uniquify(Path(os.getcwd()) / Path("{}_{}".format(filename, date)))

    print("image_dir_name = {}".format(image_dir_name))
    os.mkdir(image_dir_name)

    return image_dir_name


#
# Создать каталог для изображений.
# Сохранить в каталог все изображения, которые есть в файле документа
#
def save_images(filepath, date):
    doc = Document(filepath)
    image_dir_name = create_image_dir(os.path.basename(filepath)[:-5], date)
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
        img_name = uniquify(Path("{}".format(image_dir_name)) / Path("{}_{}".format(str(count + 1).zfill(num_lengh),
            os.path.basename(doc.part.related_parts[content_id].partname))))
        img_data = doc.part.related_parts[content_id]._blob

        with open(img_name, 'wb') as fp:
            fp.write(img_data)
    print("{} images has been saved.".format(total))

    return image_dir_name


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
def img2txt_on_lang(dir_path, language):
    # Отобразить сообщение для пользователя
    print("img2txt_on_lang ({})".format(language))
    # Путь к каталогу с изображениями
    d_path = Path(dir_path)
    # Создать подкаталог для текстовых файлов на целевом языке
    # Имя подкаталога для текстовых файлов
    text_dir = d_path / "text"
    # Имя подкаталога для текстов на текущем распознаваемом языке
    lang_dir = text_dir / "{}".format(language)
    # Если подкаталог ещё не существует - создать его
    if not os.path.exists(lang_dir):
        os.makedirs(lang_dir, exist_ok=True)

    # TODO: Ускорить проверку уже распарсенного
    # Перечислить все файлы изображений
    for img in [f for f in listdir(d_path) if isfile(join(d_path / f))]:
        # TODO: Вставить прогрессбар
        # Собрать полный путь к файлу изображения
        img_name = d_path / img
        # Собрать полный путь к файлу с распозанным текстом
        txt_file_name = lang_dir / "{}.{}.txt".format(img, language)
        print(txt_file_name)
        # Если изображение ещё не распознано - запустить распознавание
        if not os.path.exists(txt_file_name) or os.stat(txt_file_name).st_size == 0:
            result, scale = WidExtractfunctions.image_to_string_only(img_name, lang=language)
            if result:
                with open(txt_file_name, 'w', encoding='utf-8') as fp:
                    fp.write(result)
        else:
            continue
    return lang_dir


# dir_path - путь к каталогу с изображениями
def img2txt(dir_path):
    return img2txt_on_lang(dir_path, 'eng'), img2txt_on_lang(dir_path, 'rus')


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
    for txt_file in [f for f in listdir(txtdir) if isfile(join(txtdir, f))]:
        with open(join(txtdir, txt_file), 'r', encoding='utf-8') as fp:
            text = fp.read()
            results = find_timestamps(text, date)
            if results:
                print(
                    "Found in {}:".format(txt_file))
                for item in results:
                    print(item.strftime('%d/%m/%Y'))


# Проверить file на наличие на скриншотах дат не позже date
def check_files(file_mask, date):
    # 1 Вывести задание на экран
    print("Task: to find the timestamps earlier than {} at the file(s) `{}`.\n".format(date, file_mask))

    # Найти все файлы, удовлетворяющие маске
    for file in glob.iglob(file_mask, recursive=True):
        if os.path.isfile(file):
            print("Processing file {}...\n".format(file))
            # 2 Сохранить картинки в каталог
            img_dir = save_images(file, date)

            # 3 Получить текст из картинок
            if os.path.exists(img_dir):
                txt_eng_dir, txt_rus_dir = img2txt(img_dir)

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
    elif args["--get-text"]:
        if args["<img-dir>"]:
            if os.path.exists(args["<img-dir>"]):
                img2txt(args["<img-dir>"])
            else:
                print("Directory {} with texts is not exist...".format(args["<img-dir>"]))
        else:
            print("Please point image directory to text recognize.")
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
    colorama.init()
    try:
        arguments = docopt.docopt(__doc__, version='ScrTimeCheck ' + ScrTimeCheck_version)
        check_arguments(arguments)
    except docopt.DocoptExit as e:
        print(e)
