#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Local:
import ConfigurationELSA as elsa
#Libraries:
from contextlib import contextmanager
import os
import datetime
import zipfile
import re
import shutil 

ARCHIVE_FILE_NAME_PREFIX = 'backup-'
ARCHIVE_FILE_NAME_DATE_FORMAT = '%Yy%mm%dd-%Hh%Mm%Ss'
ARCHIVE_FILE_NAME_SUFFIX = ''
ARCHIVE_TYPE = "zip"  # Can be tar, bztar, gztar

@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def create_backup_zip():
    """
    Creates an archive of the DIR_USER_DATA and saves it to DIR_WEB_TEMP.
    Returns absolute path to the generated file.
    """
    today = datetime.datetime.today()
    
    archive_output_dir = os.path.abspath(elsa.DIR_WEB_TEMP)
    archive_input_dir = os.path.abspath(elsa.DIR_USER_DATA)
    archive_output_file_name = today.strftime(ARCHIVE_FILE_NAME_PREFIX
                               + ARCHIVE_FILE_NAME_DATE_FORMAT
                               + ARCHIVE_FILE_NAME_SUFFIX)
    archive_output_file_name = os.path.join(archive_output_dir,
                                            archive_output_file_name)

    # Switching working directory to save to the right place
    # A context is used to guarantee we will go back to the original place
    #   afterwards
    with cd(archive_input_dir):
        shutil.make_archive(archive_output_file_name, ARCHIVE_TYPE)
    return os.path.join(archive_output_dir,
                        archive_output_file_name + '.' + ARCHIVE_TYPE)

def restore_from_zip(fname):
    """
    Restores from the file in fname. Will erase the current data.
    Assumes all files have been properly closed and won't change
    durint the restoration.
    """
    archive_output_dir = os.path.abspath(elsa.DIR_WEB_TEMP)
    data_dir = os.path.abspath(elsa.DIR_USER_DATA)
    zip_ref = load_zip_file(os.path.join(archive_output_dir, fname))
    if not __is_zip_a_backup(zip_ref):
        print("Received an invalid backup .zip. Aborting restore.")
        return False
    
    print("Starting recovery process")
    try:
        shutil.rmtree(elsa.DIR_USER_DATA)
    except shutil.Error:
        print("Unable to delete current data before restoration. \
              Please delete user data then attempt restore again.")
        return False
    zip_ref.extractall(elsa.DIR_USER_DATA)
    return True

def load_zip_file(file_path):
    """
    Returns a zipfile reference. If an error occurs, will return False
    """
    try:
        zip_ref = zipfile.ZipFile(file_path, "r")
    except zipfile.BadZipfile as AttributeError:
        return False
    return zip_ref

def check_zip_backup(file_path):
    """
    Returns true if the file appears to be a valid backup, false otherwise
    """
    zip_ref = load_zip_file(os.path.join(file_path))
    return __is_zip_a_backup(zip_ref)
    

def __is_zip_a_backup(zip_ref):
    """
    Returns true if the .zip is a valid backup, false otherwise
    """
    if zip_ref == False:
        return False
    file_list = zip_ref.namelist()
    if 'csv/' not in file_list or 'rrd/' not in file_list:
        return False

    if number_top_dirs(file_list) != 2:
        return False 
    
    return True

def number_top_dirs(file_list):
    output = 0
    for i in file_list:
        if i.count('/') == 1 and re.search("/$", i) is not None:
            output = output + 1
    return output

if __name__ == "__main__":
    restore_from_zip("signal-desktop-mac-1.5.2.zip")
