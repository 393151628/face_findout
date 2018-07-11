# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import os
import socket
import struct
import cv2
import face_recognition
import time
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

UPLOAD_PATH = '/data/img/upload'
VIDEO_IMG_PATH = '/data/img/tmp'
VIDEO_LIST_PATH = ['rtsp://172.31.34.43/stream2']
STORAGE_PATH = 'http://172.28.50.66:11111'

@app.route('/api/upload', methods=['POST', 'GET'])
def uploads():
    if request.method == 'POST':
        f = request.files['file']
        t = int(time.time())
        upload_path = os.path.join(UPLOAD_PATH, str(t) + '_' + f.filename)
        f.save(upload_path)
        return upload_path


@app.route('/api/video_list', methods=['POST', 'GET'])
def get_video_list():
    if request.method == 'GET':
        result = []
        for p in VIDEO_LIST_PATH:
            video_img_path = get_video_img(p)
            data = {
                'img': STORAGE_PATH + video_img_path,
                'tunnel': p,
            }
            result.append(data)

        return jsonify(result)


def get_video_img(v):
    start = time.time()
    cap = SingletonModel(v)
    end = time.time()
    print(end - start)
    if cap.isOpened():
        ret, frame = cap.read()
        ip = v.split('/')[2]
        ip_int = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])
        t = time.time()
        path = os.path.join(VIDEO_IMG_PATH, str(t) + '_' + str(ip_int) + '_' + 'a.jpg')
        print(path)
        res = cv2.imwrite(path, frame)
        if res:
            return path
        else:
            return 'error: not save img'


class SingletonModel(object):
    tunnul_list = {}

    def __new__(cls, v, *args, **kwd):
        if v in SingletonModel.tunnul_list:
            return SingletonModel.tunnul_list[v]
        else:
            SingletonModel.tunnul_list.update({v: cv2.VideoCapture(v)})
            return SingletonModel.tunnul_list[v]


@app.route('/api/conn_websocket/')
def conn_websocket():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            message = ws.receive()
            ws.send(message)
    return 'success'


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8888, debug=True)
    http_server = WSGIServer(('0.0.0.0', 8888), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
