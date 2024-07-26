#!/usr/local/bin/python3

import sys,os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import urllib3

from syncPhoto import Config

urllib3.disable_warnings()
from source.mi import SourceHelper
from target.photoPrism import TargetHelper
import os




if __name__ == '__main__':
    if not os.path.isdir(Config.SYNC_DIR):
        os.mkdir(Config.SYNC_DIR)
    source_helper = SourceHelper.INIT()
    photo_paths = source_helper.sync_photo()
    print(photo_paths)
    #todo 1、已经上传的不需要上传 2、AI识别需要上传的照片
    TargetHelper.sync_photo(photo_paths)


