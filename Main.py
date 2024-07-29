#!/usr/local/bin/python3
import sys, os

import Config

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import urllib3

urllib3.disable_warnings()

from source.mi import SourceHelper
from target.photoPrism import TargetHelper
import os

if __name__ == '__main__':
    for account in Config.ACCOUNTS:
        username = account['username']
        password = account['password']
        device_id = account['device_id']
        sync_album_name = account['sync_album_name']
        sync_dir = account['sync_dir']
        if len(sync_dir) != 0 and not os.path.isdir(Config.SYNC_DIR):
            os.mkdir(sync_dir)
        source_helper = SourceHelper.INIT(username, password, device_id, sync_dir)
        photo_paths = source_helper.sync_photo()
        print(photo_paths)
        # todo 1、已经上传的不需要上传 2、AI识别需要上传的照片
        TargetHelper.sync_photo(photo_paths=photo_paths, username=Config.PP_USERNAME, password=Config.PP_PASSWORD,
                                base_url=Config.PP_BASE_URL, sync_dir=sync_album_name)
