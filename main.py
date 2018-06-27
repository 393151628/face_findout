# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import os
import socket
import struct
import cv2
import face_recognition
import time

app = Flask(__name__)

UPLOAD_PATH = '/data/img/upload'
VIDEO_IMG_PATH = '/data/img/tmp'
VIDEO_LIST_PATH = ['rtsp://172.31.34.43/stream1']


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
                'img': video_img_path,
                'tunnel': p,
            }
            result.append(data)

        return jsonify(result)


def get_video_img(v):
    cap = cv2.VideoCapture(v)

    if cap.isOpened():
        ret, frame = cap.read()
        ip = v.split('/')[2]
        ip_int = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])
        path = os.path.join(VIDEO_IMG_PATH, '_', ip_int, '_', 'a.jpg')
        res = cv2.imwrite(path, frame)

        cap.release()
        if res:
            return path
        else:
            return 'error: not save img'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
