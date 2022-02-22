#!/usr/bin/env python3
# coding: utf-8
""" Module for timestamps on screenshots checking.
Copyleft 2021-22 by Roman M. Yudichev (industrialSAST@ya.ru)

Usage:
    ScrTimeCheck.py -c | --check <docx-file-mask> <date>
    ScrTimeCheck.py -h | --help
    ScrTimeCheck.py -v | --version
    
Options:
    -c --check     Комплексная проверка файлов на наличие скриншотов с датами ранее указанной.
    -h --help      Show this screen.
    -v --version   Show version.

    Примеры:
         ScrTimeCheck.py -c topdir/**/*.doc*  "2021-01-10" - найти рекурсивно в файлах doc* _всех_ подкаталогов
                каталога topdir любой степени вложенности (маска "**") скриншоты с датами ранее 10 января 2021 года.

"""
import glob
import datetime
import shutil
import datetime_matcher
import docopt
from docx import Document
import os
from pathlib import Path
from PIL import Image
import pytesseract
from loguru import logger
import progressbar

ScrTimeCheck_version = '2.2.0'
img_subdir_name = 'img'
findings_dir_name = 'found_before_{}'

# Вернуть имя с уникальным префиксом типа "(1)", если есть дубликат
def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 0

    while os.path.exists(path):
        if counter > 0:
            # logger.debug("Output directory already exist: {}".format(path))
            path = "{}({}){}".format(filename, str(counter), extension)
        counter += 1

    return path

def create_work_dir(filename, date):
    p = uniquify(Path(os.getcwd()) / Path("{}_{}".format(filename, date)))
    # logger.debug("Working directory = {}".format(p))
    os.makedirs(p)
    return p


def create_image_dir(work_dir):
    p = Path(work_dir) / img_subdir_name
    os.makedirs(p)
    return p

# Создать каталог для найденных скриншотов-"косяков"
def create_findings_dir(work_dir, findings_dir_name):
    p = Path(work_dir) / Path(findings_dir_name)
    logger.info("Directory for images with wrong dates = {}".format(p))
    os.makedirs(p)
    return p

#
# Создать каталог для изображений.
# Сохранить в каталог все изображения, которые есть в файле документа
# TODO: увеличить чёткость и разрешение изображения для повышения качества распознавания
# https://stackoverflow.com/questions/32454613/python-unsharp-mask
#
def save_images(filepath, dir):
    doc = Document(filepath)

    total = 0
    # Количество разрядов в индексе картинки
    num_lengh = len(str(len(doc.inline_shapes)))

    # Количество изображений
    num_images = len(doc.inline_shapes)
    logger.info("Writing {} images from {} document to separate files...".format(str(num_images), filepath))

    with progressbar.ProgressBar(max_value=num_images) as bar:
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
            bar.update(count)


# Грубая проверка на опечатки и ошибки распознавания
def sounds_reasonable(item):
    # logger.error(item)
    past = datetime.date(1970, 1, 1)
    future = datetime.date(2099, 12, 31)

    present = item.date()
    # Проверка на "до-Unix'овую эру" и на "будущее"
    return past < present < future


# Поиск таймстампов в строке
def find_timestamps(text, date, lang):
    searches = [r'%d(\/|\.|\\|\/)%M(\/|\.|\\|\/)%Y',
                r'%Y(\/|\.|\\|\/)%d(\/|\.|\\|\/)%M',
                r'%Y']

    dtmatcher = datetime_matcher.DatetimeMatcher()

    results = []
    for srch in searches:
        dates = dtmatcher.extract_datetimes(srch, text)
        if not dates is None:
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
    logger.info("dir_path = {}".format(dir_path))
    logger.info("text_dir_path = {}".format(text_dir_path))
    # logger.info("language = {}".format(language))
    # logger.info("Start text recognition on [{}] language...".format(language))
    # Путь к каталогу с изображениями
    d_path = Path(dir_path)
    # Создать подкаталог для текстовых файлов на целевом языке
    # Имя подкаталога для текстов на текущем распознаваемом языке
    lang_dir = Path(text_dir_path) / Path("{}".format(language))
    # Если подкаталог ещё не существует - создать его
    if not os.path.exists(lang_dir):
        os.makedirs(lang_dir, exist_ok=True)

    count = len([name for name in os.listdir(dir_path) if os.path.isfile(Path(dir_path) / Path(name))])
    with progressbar.ProgressBar(max_value=count) as bar:
        # Перечислить все файлы изображений
        for i, img in enumerate([f for f in os.listdir(dir_path) if os.path.isfile(Path(dir_path) / Path(f))]):
            # Собрать полный путь к файлу изображения
            img_name = d_path / img
            # Собрать полный путь к файлу с распознанным текстом
            txt_file_name = lang_dir / "{}.{}.txt".format(img, language)
            # logger.info(txt_file_name)
            # Если изображение ещё не распознано - запустить распознавание
            if not os.path.exists(txt_file_name) or os.stat(txt_file_name).st_size == 0:
                result = pytesseract.image_to_string(Image.open(img_name), lang=language)
                if result:
                    with open(txt_file_name, 'w', encoding='utf-8') as fp:
                        fp.write(result)
            else:
                continue
            bar.update(i)
    return lang_dir


# dir_path - путь к каталогу с изображениями
def img2txt(img_dir_path, text_dir_path):
    return img2txt_on_lang(img_dir_path, text_dir_path, 'eng'), img2txt_on_lang(img_dir_path, text_dir_path, 'rus')


def restore_img_filepath(file_path):
    dir, file = os.path.split(file_path)
    file_name = os.path.basename(file)[:-8]
    dir_name = Path(dir[:-9]) / Path("img")

    return Path(dir_name) / Path(file_name)

# Скопировать артефакты с "протухшими" датами в спец. каталог
# TODO: копировать скриншоты с найденными датами в подкаталог c именем типа "Found_before_%Y-%M-%d"
def copy_to_findings(file_path, dir):
    # Восстановить имя файла изображения по имени текстового файла, в котором найдены косяки
    img_file_path = restore_img_filepath(file_path)
    dest = Path(dir) / Path(os.path.basename(img_file_path))
    if os.path.exists(img_file_path):
        shutil.copyfile(img_file_path, dest)


# Для каждого текстового файла в указанном каталоге
# распознать дату в каждой строке
def process_txt_dir(txtdir, date, lang, dir):
    logger.info("Starting text files processing...")
    for txt_file in [f for f in os.listdir(txtdir) if os.path.isfile(Path(txtdir) / Path(f))]:
        recognized_text_file_path = Path(txtdir) / Path(txt_file)
        with open(recognized_text_file_path, 'r', encoding='utf-8') as fp:
            text = fp.read()
            results = find_timestamps(text, date, lang)
            if results:
                logger.info("Found in {}:".format(txt_file))
                copy_to_findings(recognized_text_file_path, dir)
                for item in list(set(results)):
                    logger.info(item.strftime('%Y-%m-%d'))


# Вывести задание на экран
def show_task(f_mask, date):
    logger.info("Task: to find the timestamps earlier than {} at the file(s) `{}`.\n".format(date, f_mask))
    count_files = 0
    for file in glob.iglob(f_mask, recursive=True):
        if os.path.isfile(file):
            count_files +=1
    if count_files == 0:
        logger.info("There are no files found.\nExit whithout any work done.")
    else:
        if count_files == 1:
            logger.info("There is one file found.")
        else:
            logger.info("There are {} files found.".format(count_files))


# Проверить file на наличие на скриншотах дат не позже date
def check_files(file_mask, date):
    show_task(file_mask, date)

    # Найти все файлы, удовлетворяющие маске
    for file in glob.iglob(file_mask, recursive=True):
        if os.path.isfile(file):
            # Создать рабочий каталог
            work_dir = create_work_dir(os.path.basename(file), date)
            logger.add(Path(work_dir) / Path("date_in_images_report.log"), format = "{time} {message}", level = "INFO", rotation="100 KB", compression="zip")
            logger.info("Processing file {}...\n".format(file))
            # Создать каталог для изображений
            image_dir_name = create_image_dir(work_dir)
            # Создать каталог для найденного
            current_findings_dir_name = create_findings_dir(work_dir, findings_dir_name.format(date))
            # logger.debug("current_findings_dir_name = ".format(current_findings_dir_name))
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
                    logger.info("Finding dates in English text...")
                    process_txt_dir(txt_eng_dir, date, "eng", current_findings_dir_name)
                if os.path.exists(txt_rus_dir):
                    logger.info("Finding dates in Russian text...")
                    process_txt_dir(txt_rus_dir, date, "rus", current_findings_dir_name)


def check_arguments(args):
    if args["--check"] and args["<docx-file-mask>"] and args["<date>"]:
        if args["<date>"]:
            check_files(args["<docx-file-mask>"], args["<date>"])
        else:
            logger.debug('Please point the deadline date ("YYYY-MM-DD").')
    else:
        logger.debug("Please point all the arguments correctly.")
        logger.debug(args)


###############################################################################
if __name__ == "__main__":
    try:
        arguments = docopt.docopt(__doc__, version='ScrTimeCheck ' + ScrTimeCheck_version)
        check_arguments(arguments)
    except docopt.DocoptExit as e:
        print(e)
