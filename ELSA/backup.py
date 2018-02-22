#!/usr/bin/env python
# -*- coding: utf-8 -*-
from shutil import make_archive
from contextlib import contextmanager
import os
import datetime
import ConfigurationELSA as elsa

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
    """Creates an archive of the DIR_USER_DATA and saves it to DIR_WEB_TEMP. Returns absolute path to the generated file."""
    today = datetime.datetime.today()
    
    archive_output_file_name = today.strftime(ARCHIVE_FILE_NAME_PREFIX + ARCHIVE_FILE_NAME_DATE_FORMAT + ARCHIVE_FILE_NAME_SUFFIX)
    archive_output_dir = os.path.abspath(elsa.DIR_WEB_TEMP)
    archive_input_dir = os.path.abspath(elsa.DIR_USER_DATA)

    # Switching working directory to save to the right place
    # A context is used to guarantee we will go back to the original place afterwards
    with cd(archive_output_dir):
        make_archive(archive_output_file_name, ARCHIVE_TYPE,
                     archive_output_dir, archive_input_dir)
    return os.path.join(archive_output_dir, archive_output_file_name) + '.' + ARCHIVE_TYPE
