#coding=utf-8
import datetime

import os

import numpy
from celery import Celery
from celery.bin import worker as celery_worker
import time
import redis
import cv2

import uuid
from config import *

# broker = 'amqp://admin:admin@172.31.43.49/mytest'
broker = 'redis://172.31.43.49:6379/0'
backend = 'redis://172.31.43.49:6379/1'
app = Celery('my_celery_task',  broker=broker, backend=backend)

# pool = redis.ConnectionPool(host='172.28.50.91', port=6379, db=2)


@app.task(bind=True)
def video_loop_handle(self, url, imgs):
    import face_recognition
    face_encodings_knows = img_encoding(imgs, face_recognition)
    cap = cv2.VideoCapture(url)
    timer = 0
    appear = [ False for i in face_encodings_knows ]
    last_frame = 0
    while cap.isOpened():
        this_have = []
        ok, frame = cap.read()  # 读取一帧数据
        timer += 1
        # print('timer:', timer)
        if not ok:
            break
        if timer % time_interval == 0:
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_frame = frame[:, :, ::-1]
            faceRects = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=0, model="cnn")
            if len(faceRects) > 0:
                face_encodings = face_recognition.face_encodings(rgb_frame, faceRects)
                for face_encoding in face_encodings:
                    face_res = face_recognition.face_distance(face_encodings_knows, face_encoding)
                    k = face_res.min()
                    f = face_res.argmin()
                    print('kkkkkk:', k)
                    if k < 0.4:
                        if appear[f]:
                            this_have.append(f)
                        else:
                            uid = str(uuid.uuid1())
                            result_path = os.path.join(RESULT_IMG_PATH, uid + '_' + 'result.jpg')
                            cv2.imwrite(result_path, frame)
                            data = set_data(url, f, imgs, result_path, 'start')
                            print('data:', data)
                            self.update_state(state="PROGRESS", meta=data)
                            appear[f] = True
                            this_have.append(f)
            for idx, i in enumerate(appear):
                if i and idx not in this_have:
                    uid = str(uuid.uuid1())
                    result_path = os.path.join(RESULT_IMG_PATH, uid + '_' + 'result.jpg')
                    cv2.imwrite(result_path, last_frame)
                    data = set_data(url, idx, imgs, result_path, 'end')
                    print('############')
                    self.update_state(state="PROGRESS", meta=data)
                    appear[idx] = False
            last_frame = frame


def set_data(url, f, imgs, result_path, t):
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {'title': v['title'] for v in VIDEO_LIST_PATH if v['tunnel1'] == url}
    data['url'] = url
    data['img'] = int(f)
    data['path'] = STORAGE_PATH + imgs[int(f)].replace(BASE_PATH, '')
    data['type'] = t
    data['time_str'] = time_str
    data['result_path'] = STORAGE_PATH + result_path.replace(BASE_PATH, '')
    return data


def img_encoding(imgs, face_recognition):
    result = []
    for img in imgs:
        frame = face_recognition.load_image_file(img)
        face_locations = face_recognition.face_locations(frame, number_of_times_to_upsample=0, model="cnn")
        if len(face_locations) > 0:
            face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
            result.append(face_encoding)
        else:
            result.append(numpy.array((0,0,0)))
    return result




def worker_start():
    worker = celery_worker.worker(app=app)
    worker.run(broker=broker, concurrency=4,
               traceback=False, loglevel='INFO')


if __name__ == "__main__":
    worker_start()