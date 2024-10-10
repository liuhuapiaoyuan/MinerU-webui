import os
import zipfile


import magic_pdf.model as model_config

from pdf2image import convert_from_path



def zip_directory(zip_file, directory_path, base_path):
    """
    递归压缩目录
    :param zip_file: zipfile.ZipFile 对象
    :param directory_path: 当前目录路径
    :param base_path: 基础路径，用于计算相对路径
    """
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            # 递归处理子目录
            zip_directory(zip_file, item_path, base_path)
        else:
            # 添加文件
            zip_file.write(item_path, os.path.relpath(item_path, base_path))

def zip_files_and_dirs(files: list, zip_file_path: str):
    """
    压缩文件和目录
    :param files: 要压缩的文件或目录列表
    :param zip_file_path: 压缩文件路径
    :return: None
    """
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            if os.path.isfile(file):
                zip_file.write(file, os.path.basename(file))
            elif os.path.isdir(file):
                zip_directory(zip_file, file, os.path.dirname(file))


def export_zip(md_path):
    # 获得父级路径
    parent_path = os.path.dirname(md_path)
    # 获得文件名
    file_name = os.path.basename(md_path)
    # image_dir
    images_dir = os.path.join(parent_path,  "images")
    # 压缩文件
    zip_file_path =os.path.join(parent_path, f"{file_name}.zip")
    zip_files_and_dirs([md_path, images_dir], zip_file_path)
    return zip_file_path