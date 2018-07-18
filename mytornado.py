# -*- coding: utf-8 -*-
import asyncio
import os
import datetime
import socket
import uuid
import time

import cv2
import numpy
import struct
import tornado.options
from tornado.web import RequestHandler, asynchronous
from tornado import gen
from tornado.options import define, options
from tornado.websocket import WebSocketHandler
from tornado.escape import json_decode, json_encode
# from mtcnn.mtcnn import MTCNN
import face_recognition
from config import *
from my_celery_task import video_loop_handle
import threading

# detector = MTCNN()
# 比检测位置向外扩一些


define("port", default=8001, type=int)


# .\ffmpeg.exe -y -i .\hamilton_clip.mp4 -ss 00:0:30.0 -t 00:01:00.0 -acodec copy -vcodec copy -async 1 bjysxyt1.mp4


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
        # print('data:', data)
        # print('img_encoding:', e - s)
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

    def post(self):
        data = json_decode(self.request.body)
        ids = data.get('ids')
        start = data.get('start')
        end = data.get('end')
        img = data.get('img')
        video_files = find_video_file()
        #
        print(data, '#######################')
        self.write('OK')


def find_video_file():
    return []


app = tornado.web.Application([
    (r"/api/conn_websocket/", ConnectWSHandler),
    (r"/api/upload", FileUploadHandler),
    (r"/api/video_list", VideoHandler),
    (r"/api/file_list", FileHandler),
],
    debug=True
)

if __name__ == '__main__':
    # tornado.options.parse_command_line()

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
