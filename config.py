# -*- coding: utf-8 -*-
BASE_PATH = r'/home/zhangyb'
UPLOAD_PATH = BASE_PATH + '/data/img/upload'
VIDEO_IMG_PATH = BASE_PATH + '/data/tmps'
RESULT_IMG_PATH = BASE_PATH + '/data/result'
VIDEO_FILE_PATH = {
    'abc':  '/home/zhangyb/data/video/'
}
VIDEO_LIST_PATH = [
    {
        'title': '1号楼道',
        'tunnel1': 'rtsp://172.31.43.47/stream1',
        'tunnel2': 'rtsp://172.31.43.47/stream2',
        'id': 'abc',
        'file_path': '/home/zhangyb/data/video/',
    }
]

STORAGE_PATH = 'http://172.31.43.49:8000'
time_interval = 10

LISENCE_PATH = 'license/miyao.syswin'