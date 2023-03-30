#!/usr/bin/env python3
# coding: utf-8
""" Module for screenshots replacement.
Copyleft 2021-22 by Roman M. Yudichev (industrialSAST@ya.ru)

Usage:
    screenshot_replacer.py <file> <directory>
    screenshot_replacer.py -h | --help
    screenshot_replacer.py -v | --version

Options:
    <file>         Файл, в котором выполнить замену скриншотов.
    <directory>    Каталог с обновлёнными скриншотами.
    -h --help      Show this screen.
    -v --version   Show version.

"""
import shutil
import zipfile
import glob
import datetime
import shutil
import datetime_matcher
import docopt
from docx import Document
import os
from pathlib import Path
from PIL import Image
import platform
import pytesseract
from loguru import logger
from tqdm import tqdm
from joblib import Parallel, delayed

screenshot_replacer_version = '0.1'

exit_codes = {
    0: "Success.",
    1: "Не указаны никакие аргументы",
    2: "",
    3: "",
    4: "Файл, указанный в качестве аргумента, не существует.",
    5: "Директория, указанная в качестве аргумента, не существует."
}



def process_files(docx_file, images_dir):
    # Создаем временную директорию, куда будем извлекать содержимое файла docx
    temp_dir = os.path.join(os.path.dirname(docx_file), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Извлекаем содержимое файла docx во временную директорию
    with zipfile.ZipFile(docx_file, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # Проходим по всем изображениям в директории с содержимым файла docx
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".jpeg") or file.endswith(".jpg") or file.endswith(".png"):
                image_path = os.path.join(root, file)
                image_name = os.path.splitext(file)[0]

                # Ищем файл с таким же именем в директории с изображениями
                image_file = None
                for root2, dirs2, files2 in os.walk(images_dir):
                    for file2 in files2:
                        if file2.startswith(image_name):
                            image_file = os.path.join(root2, file2)
                            break
                    if image_file:
                        break

                # Если нашли файл с таким же именем, заменяем старое изображение на новое
                if image_file:
                    shutil.copyfile(image_file, image_path)

    # Создаем новый файл docx и сохраняем в него изменения
    new_docx_file = os.path.join(os.path.dirname(docx_file), "new_" + os.path.basename(docx_file))
    with zipfile.ZipFile(new_docx_file, "w") as zip_ref:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zip_ref.write(file_path, os.path.relpath(file_path, temp_dir))

    # Удаляем временную директорию
    shutil.rmtree(temp_dir)

    # Удаляем старый файл docx и переименовываем новый
    # os.remove(docx_file)
    # os.rename(new_docx_file, docx_file)



def check_arguments(args):
    if args["<file>"]:
        if not os.path.exists(args["<file>"]):
            logger.info(f"Please point argument 'file' correctly (file {args['<file>']} is not exist now.")
            exit(4)

        if args["<directory>"]:
            if not os.path.isdir(args["<directory>"]):
                logger.info(f"Please point argument 'directory' correctly (directory {args['<directory>']} is not exist now.")
                exit(5)

    else:
        logger.debug("Please point all the arguments correctly.")
        logger.debug(args)

    process_files(args["<file>"], args["<directory>"])


###############################################################################
if __name__ == "__main__":
    try:
        arguments = docopt.docopt(__doc__, version=f"screenshot_replacer {screenshot_replacer_version}")
        check_arguments(arguments)
    except docopt.DocoptExit as e:
        print(e)

