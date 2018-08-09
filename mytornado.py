# -*- coding: utf-8 -*-
import asyncio
import os
import datetime
import socket
import uuid
import time

import cv2
import struct
import tornado.options
from tornado.web import RequestHandler
from tornado.options import define, options
from tornado.websocket import WebSocketHandler
from tornado.escape import json_decode, json_encode
from config import *
from my_celery_task import video_loop_handle
import threading
from decryption import Dencryption
from hashlib import sha1
import face_recognition
from io import BytesIO
from PIL import Image
import numpy as np

# detector = MTCNN()
# 比检测位置向外扩一些

define("port", default=8001, type=int)


# .\ffmpeg.exe -y -i .\hamilton_clip.mp4 -ss 00:0:30.0 -t 00:01:00.0 -acodec copy -vcodec copy -async 1 bjysxyt1.mp4


def init_args():
    global key
    global dencryption
    dencryption = Dencryption()
    with open(LISENCE_PATH, 'rb') as f:
        key = f.read().decode('utf8')


# create_session_id = lambda: sha1(bytes('%s%s' % (os.urandom(16), time.time()), encoding='utf-8')).hexdigest()
def create_session_id():
    return sha1(bytes('%s%s' % (os.urandom(16), time.time()), encoding='utf-8')).hexdigest()


def check_lisence(func):
    def warrper(*args, **kwargs):
        handler = args[0]
        cookie = handler.get_cookie('lisence')
        if not cookie:
            print('##################', cookie)
            if dencryption.verifykey(key) == 1:
                random_str = create_session_id()
                handler.set_cookie('lisence', random_str, max_age=60)
                func(*args, **kwargs)
            else:
                handler.render('demo.html')
            # args[0].write('need buy')
        else:
            func(*args, **kwargs)

    return warrper


class ConnectWSHandler(WebSocketHandler):
    socket_handler = set()  # 用来存放在线用户的容器
    socket_res_dict = {}
    socket_thread_dict = {}

    def open(self):
        print('connect!')
        self.socket_handler.add(self)
        self.socket_res_dict[self] = []
        self.socket_thread_dict[self] = []
        print('socket_handler:', self.socket_handler)

    def on_message(self, message):
        data = json_decode(message)
        # data: {'img': ['img1.jpg', 'img2.jpg'], 'video': ['tunel1', 'tunel2']}
        print('data:', data)
        # print('img_encoding:', e - s)
        if data['type'] == 'file':
            img = ['/home/zhangyb/data/video/imp.jpg']
            file = '/home/zhangyb/data/video/aaa.mp4'
            ret = video_loop_handle.apply_async(args=[file, img])
            t = MyThread(self, ret)
            t.start()
            self.socket_thread_dict[self].append(t)
        else:
            for url in data['video']:
                # self.video_find_out(url, face_encodings_knows, data['img'])
                res = video_loop_handle.apply_async(args=[url, data['img']])
                self.socket_res_dict[self].append(res)
                t = MyThread(self, res)
                t.start()
                self.socket_thread_dict[self].append(t)
                print('当前连接数：', len(self.socket_handler))

    def on_close(self):
        print('close!')
        for r in self.socket_res_dict[self]:
            r.revoke(terminate=True)

        for t in self.socket_thread_dict[self]:
            t.switch = False
        self.socket_handler.remove(self)
        self.socket_res_dict.pop(self)
        self.socket_thread_dict.pop(self)
        print('socket_handler:', self.socket_handler)

    def check_origin(self, origin):
        return True  # 允许WebSocket的跨域请求

    # def video_find_out(self, url, face_encodings_knows, imgs):
    #     cap = cv2.VideoCapture(url)
    #     timer = 0
    #     print('########')
    #     while cap.isOpened() and self.switch:
    #         ok, frame = cap.read()  # 读取一帧数据
    #         timer += 1
    #         # print('timer:', timer)
    #         if not ok:
    #             break
    #         if timer % time_interval == 0:
    #             # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    #             rgb_frame = frame[:, :, ::-1]
    #             s = time.time()
    #             # faceRects = detector.detect_faces(rgb_frame)
    #             # faceRects = face_recognition.face_locations(rgb_frame)
    #             faceRects = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=0, model="cnn")
    #             e = time.time()
    #             # print('detect:', float('%.5f' % (e - s)))
    #             if len(faceRects) > 0:
    #                 # x, y, w, h = faceRects[0]['box']
    #                 # for faceRect in faceRects:
    #                 # top, right, bottom, left = faceRect
    #                 s = time.time()
    #                 # face_encodings = face_recognition.face_encodings(rgb_frame[y - t: y + h + t, x - t: x + w + t])
    #                 face_encodings = face_recognition.face_encodings(rgb_frame, faceRects)
    #                 e = time.time()
    #                 # print('face_encodings:', float('%.5f' % (e - s)), '------', len(face_encodings))
    #                 # if len(face_encodings) == 0:
    #                 #     cv2.imwrite('/home/zhangyb/tmp/test.jpg', frame)
    #                 #     cv2.imwrite('/home/zhangyb/tmp/test22.jpg', rgb_frame[top:bottom, left:right])
    #                 #     break
    #                 for face_encoding in face_encodings:
    #                 # if len(face_encodings) != 0 and face_encodings_knows:
    #                 #     face_encoding = face_encodings[0]
    #                     s = time.time()
    #                     face_res = face_recognition.face_distance(face_encodings_knows, face_encoding)
    #                     e = time.time()
    #                     # print('face_distance:', float('%.5f' % (e - s)))
    #                     k = face_res.min()
    #                     f = face_res.argmin()
    #                     print('kkkkkk:', k)
    #                     if k < 0.4:
    #                         uid = str(uuid.uuid1())
    #                         time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #                         result_path = os.path.join(RESULT_IMG_PATH, uid + '_' + 'result.jpg')
    #                         cv2.imwrite(result_path, frame)
    #                         data = {'title': v['title'] for v in VIDEO_LIST_PATH if v['tunnel1'] == url}
    #                         data['url'] = url
    #                         data['img'] = int(f)
    #                         data['path'] = STORAGE_PATH + imgs[int(f)].replace(BASE_PATH, '')
    #                         data['time_str'] = time_str
    #                         data['result_path'] = STORAGE_PATH + result_path.replace(BASE_PATH, '')
    #                         print('data:', data)
    #                         self.write_message(json_encode(data))


class MyThread(threading.Thread):

    def __init__(self, wbconn, celres):
        threading.Thread.__init__(self)  # 初始化父类Thread
        self.wbconn = wbconn
        self.celres = celres
        self.switch = True

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.celres.get(on_message=self.send_data, propagate=False)

    def send_data(self, body):
        if self.switch:
            print('send_data start!')
            self.wbconn.write_message(body)
            print('send message')


class FileUploadHandler(RequestHandler):
    # def set_default_headers(self):
    #     print("setting headers!!!")
    #     self.set_header("Access-Control-Allow-Origin", "*")  # 这个地方可以写域名
    #     self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    #     self.set_header('Access-Control-Allow-Methods', '*')
    @check_lisence
    def get(self):
        self.write('''
<html>
  <head><title>Upload File</title></head>
  <body>
    <form action='/api/upload' enctype="multipart/form-data" method='post'>
    <input type='file' name='file'/><br/>
    <input type='submit' value='submit'/>
    </form>
  </body>
</html>
''')

    def post(self):
        ret = []
        file_metas = self.request.files.get('file', None)  # 提取表单中‘name’为‘file’的文件元数据

        if not file_metas:
            self.write('上传失败！')
            self.finish()

        for meta in file_metas:
            filename = meta['filename']
            t = datetime.datetime.now().strftime('%Y%m%d%H%M')
            uid = str(uuid.uuid1())
            upload_path = os.path.join(UPLOAD_PATH, uid + '_' + t + '_' + filename)
            # file_path = os.path.join(upload_path, filename)
            with open(upload_path, 'wb') as up:
                up.write(meta['body'])
                # OR do other thing
            ret.append(upload_path)
        self.write(json_encode(ret))
        self.finish()


class VideoHandler(RequestHandler):
    def get(self):
        result = []
        for p in VIDEO_LIST_PATH:
            video_img_path = self.get_video_img(p['tunnel2'])
            data = {
                'img': STORAGE_PATH + video_img_path,
                'tunnel': p['tunnel1'],
                'title': p['title'],
            }
            result.append(data)

        self.write(json_encode(result))
        self.finish()

    def get_video_img(self, v):
        cap = SingletonModel(v)
        if cap.isOpened():
            ret, frame = cap.read()
            ip = v.split('/')[2]
            ip_int = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])
            t = datetime.datetime.now().strftime('%Y%m%d%H%M')
            uid = str(uuid.uuid1())
            path = os.path.join(VIDEO_IMG_PATH, uid + '_' + str(t) + '_' + str(ip_int) + '_' + 'a.jpg')
            print('path:', path)
            res = cv2.imwrite(path, frame)
            if res:
                return path
            else:
                self.write('error: not save img')
                self.finish()


class SingletonModel(object):
    tunnul_list = {}

    def __new__(cls, v, *args, **kwd):
        if v in SingletonModel.tunnul_list:
            return SingletonModel.tunnul_list[v]
        else:
            SingletonModel.tunnul_list.update({v: cv2.VideoCapture(v)})
            return SingletonModel.tunnul_list[v]


class FileHandler(RequestHandler):
    def get(self):
        # result = [os.path.join(VIDEO_FILE_PATH, file_name) for file_name in os.listdir(VIDEO_FILE_PATH)]
        result = []
        for sxt in VIDEO_LIST_PATH:
            data = {'id': sxt['id'], 'title': sxt['title']}
            result.append(data)
        self.write(json_encode(result))
        self.finish()


class CompareImg(RequestHandler):
    def post(self):
        # data = json_decode(self.request.body)
        img = self.request.files.get('img', None)
        imgs = self.request.files.get('imgs', None)
        unknow_frame = convert_binary_to_numpy(img)
        result = {
            'status', 'OK',
        }
        unknow_face_locations = find_face_location(unknow_frame)
        if len(unknow_face_locations) == 0:
            result['status'] = 'error'
            result['msg'] = 'not fount face in single img'
        else:
            know_encodings = []
            for _img in imgs:
                know_frame = convert_binary_to_numpy(_img)
                know_face_locations = find_face_location(know_frame)
                know_encodings.extend(face_recognition.face_encodings(know_frame, know_face_locations))

            unknow_encondings = face_recognition.face_encodings(unknow_frame, [unknow_face_locations[0]])
            compare_ret = face_recognition.face_distance(know_encodings, unknow_encondings[0])
            k = compare_ret.min()
            idx = compare_ret.argmin()
            if k <= 0.4:
                result['result'] = idx
            else:
                result['result'] = False

        self.write(json_encode(result))
        self.finish()


def find_face_location(frame):
    face_locations = face_recognition.face_locations(frame, number_of_times_to_upsample=0, model="cnn")
    return face_locations


def convert_binary_to_numpy(bes):
    io = BytesIO(bes)
    img = Image.open(io)
    return np.array(img)


def find_video_file():
    # file_pathes = [VIDEO_FILE_PATH[_id] for _id in ids]
    return ['/home/zhangyb/data/video/aaa.mp4']


app = tornado.web.Application([
    (r"/api/conn_websocket/", ConnectWSHandler),
    (r"/api/upload", FileUploadHandler),
    (r"/api/video_list", VideoHandler),
    (r"/api/file_list", FileHandler),
    (r"/api/compare_img", CompareImg),
],
    debug=True
)

if __name__ == '__main__':
    try:
        init_args()
    except Exception:
        print('init error')
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
