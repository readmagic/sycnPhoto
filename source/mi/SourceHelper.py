import time
import json
import os

import re

from syncPhoto.source.mi import Util
from syncPhoto.source.mi.MiClient import MiClient
from syncPhoto.Config import MI_USERNAME,MI_PASSWORD,MI_DEVICE_ID,SYNC_DIR

_domain = 'https://i.mi.com/gallery'


class INIT:

    def __init__(self):
        connector = MiClient(MI_USERNAME, MI_PASSWORD, MI_DEVICE_ID)
        self.sync_dir = SYNC_DIR
        self.logged = connector.login()
        self.connector = connector
        self.s = connector._session
        self.uuid = connector._userId
        self.update_cnt = 0  # 用于存放，本次更新了多少个文件
        self._prepare_gallery()

        # 跟踪浏览器记录，访问相册前，都会执行
    def _prepare_gallery(self):
        url = _domain + '/user/lite/index/prepare'
        headers = {
            "User-Agent": self.connector._agent,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        cookie = {'i.mi.com_istrudev': 'true',
                  'i.mi.com_isvalid_servicetoken': 'true',
                  }
        fields = {'serviceToken': self.s.cookies.get('serviceToken')}
        self.s.post(url, headers=headers, cookies=cookie, data=fields, verify=False, timeout=10)

    def _album_list(self):  # 返回相册列表，有哪些相册的目录信息
        url = _domain + '/user/album/list?ts=%d&pageNum=0&pageSize=100&isShared=false&numOfThumbnails=1' % (
                time.time() * 100)
        album_dir = os.path.join(self.sync_dir, 'album')
        if not os.path.isdir(album_dir):
            os.mkdir(album_dir)
        cookie = {'i.mi.com_istrudev': 'true',
                  'i.mi.com_isvalid_servicetoken': 'true',
                  }
        r = self.s.get(url, cookies=cookie, verify=False, timeout=30)
        ss = json.dumps(r.json(), indent=2, ensure_ascii=False)
        fname = os.path.join(album_dir, 'album_list.json')
        open(fname, 'w', encoding='utf8').write(ss)
        self.albums = r.json()['data']['albums']  # 相关相册信息，存放到公共区域
        for album in self.albums:
            name = album.get('name')
            if name is None:
                if album.get('albumId') == '2':
                    name = '截图'
                elif album.get('albumId') == '1':
                    name = '相机'
                elif album.get('albumId') == '1000':
                    name = '私有'
            name = Util.validate_title(name)
            name = os.path.join(album_dir, name)
            album['folder'] = name
            if not os.path.isdir(name):
                os.mkdir(name)

    # 给定相册id信息，起止日期，每次获得数量，获得这个相册下的所有照片/视频信息，返回结果到result里面
    def _get_one_album(self, albumId, folder, startDate='20000101', endDate='20991231', pageSize=500):
        results = []
        i = 0
        while True:
            url = _domain + '/user/galleries?ts=%d&startDate=%s&endDate=%s&pageNum=%d&pageSize=%s&albumId=%s' % (
                time.time() * 1000, startDate, endDate, i, pageSize, albumId)
            r = self.s.get(url, verify=False, timeout=40)
            fname = os.path.basename(folder) + '%d.json' % i
            fname = os.path.join(folder, fname)
            album_details = r.json()
            open(fname, 'w', encoding='utf8').write(json.dumps(album_details, indent=2, ensure_ascii=False))
            results += album_details['data']['galleries']
            if album_details['code'] == 0 and album_details['data']['isLastPage']:
                return results
            i += 1
        return results

    # 给定一个照片/视频的id信息，把它删除
    def _del_one_media(self, id):
        url = _domain + '/info/delete'
        data = {'id': id,
                'serviceToken': self.s.cookies.get('serviceToken')
                }
        r = self.s.post(url, verify=False, timeout=10, data=data)
        if not r.status_code == 200:
            return False
        result = {}
        try:
            result = r.json()
        except Exception as e:
            return False
        if not result['code'] == 0:
            return False

    # 给定一个照片/视频的id信息，以及存放到的目录和文件名，把它下载到对应地方
    def _download_one_pic(self, pic_id, fname):
        ts = int(time.time() * 1000)
        url = _domain + '/storage?ts=%d&id=%s&callBack=dl_img_cb_%d_0' % (ts, pic_id, ts)
        print(url)
        r = self.s.get(url, verify=False, timeout=10)
        if not r.status_code == 200:
            return False
        result = {}
        try:
            result = r.json()
        except Exception as e:
            print(e)
            return False
        if not result['code'] == 0:
            return False
        next_url = result['data']['url']
        print(next_url)
        r = self.s.get(next_url, verify=False, timeout=10)
        if not r.status_code == 200:
            return False
        result = {}
        try:
            reg = re.search(r'\((.+)\)', r.text)
            result = json.loads(reg.group(1))
        except Exception as e:
            print(e)
            return False
        if not result:
            return False
        real_url = result['url']
        print(real_url)
        meta = result['meta']
        try:
            block_size = 1024 * 1024
            r = self.s.post(real_url, data={'meta': meta}, verify=False, timeout=3600, stream=True)
            if not r.status_code == 200:
                return False
            total_size = int(r.headers.get('content-length', 0))
            print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
            downloaded_size = 0
            with open(fname, 'wb') as f:
                while downloaded_size < total_size:
                    data = r.raw.read(block_size)
                    f.write(data)
                    downloaded_size += block_size
        except Exception as e:
            return None
        self._del_one_media(pic_id)
        return True

    # 给定一个dict格式的相册信息，对整个相册进行下载
    def _download_album(self, folder, one_album):
        for one_pic in one_album:
            pic_name = one_pic.get('fileName')
            id = one_pic.get('id')
            if not pic_name:
                print("in download_album for %s failed, can not get fileName" % folder)
            if not id:
                print("in download_album for %s failed, can not get id" % folder)
            pic_name = os.path.join(folder, pic_name)
            print("trying to download %s" % pic_name)
            result = self._download_one_pic(pic_id=id, fname=pic_name)
            if not result:  # download_one_pic失败的话，很可能是session过期了，需要重新login下
                self.logged = self.connector.login()
                if not self.logged:
                    print("re-login failed")
                    continue
                self.s = self.connector._session
            self.update_cnt += 1

    def _get_album_info(self):  # 根据前面获得的总的相册信息（self.albums），把每个子相册的详细内容获得，并扔到self.albums_details数组中
        self.albums_details = []
        for album in self.albums:
            id = album.get('albumId')
            if not id:
                continue
            num = album.get('mediaCount')
            if not num:
                continue
            folder = album.get('folder')
            if not folder:
                continue
            print("trying for %s" % folder)
            album_details = self._get_one_album(id, folder)
            fname = os.path.basename(folder) + '.json'
            fname = os.path.join(folder, fname)
            open(fname, 'w', encoding='utf8').write(json.dumps(album_details, indent=2, ensure_ascii=False))
            self.albums_details.append({'folder': folder, 'json_name': fname, 'album': album_details})

    def sync_photo(self):
        # 开始遍历相册，获得相册列表
        self._album_list()  # 相册信息存放到了xm.albums里面
        # 获得每一个相册的具体信息
        self._get_album_info()
        # 遍历相册，逐个下载相册
        photo_pathes = []

        for one_album in self.albums_details:
            self._download_album(one_album['folder'], one_album['album'])
            photo_pathes.append(one_album['folder'])
        print("album was downloaded OK!")
        return photo_pathes
