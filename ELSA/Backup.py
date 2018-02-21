#!/usr/bin/env python
# -*- coding: utf-8 -*-
from shutil import make_archive
from contextlib import contextmanager
import os
import datetime

@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

today = datetime.datetime.today()

archive_output_file_name = today.strftime("backup-%Yy%mm%dd-%Hh%Mm%Ss")
archive_type = "zip" #Can be tar, bztar, gztar
archive_output_dir = os.path.abspath("/home/pi/akuino/ELSA/ELSA/static/temp/")
archive_input_dir = os.path.abspath("/home/pi/akuino/ELSA/data/")

# Switching working directory to save to the right place
# A context is used to guarantee we will go back to the original place afterwards
with cd(archive_output_dir):
    make_archive(archive_output_file_name, archive_type, archive_output_dir, archive_input_dir)


