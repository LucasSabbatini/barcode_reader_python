import numpy as np 
import argparse
import imutils
import cv2
import datetime
import pyzbar.pyzbar as pyzbar
import random
from util import log
import copy
import json
import time

from db_query import ClientHandler
from pymongo import MongoClient

class BarcodeDetector():
    def __init__(self, perc_to_process, mongo_url=None, output_json_path=None):
        self._camera = 0
        self._output_json_path = output_json_path
        self._perc_to_process = perc_to_process
        self._sleep_detection = 5.0

        self.log = log

        self._db_handler = ClientHandler()

        if mongo_url != None:
            self._mongo_url = mongo_url
            self._client = MongoClient(self._mongo_url)
            self._db_name = 'barcode'
            self._db = eval('self._client.' + self._db_name)
            self._collection_name = 'rasp_pi_test'
            self._db_colleciton = eval("self._db." + self._collection_name)
            self.push = self.insert_mongo
        
        elif output_json_path != None:
            self.push = self.insert_json

        else:
            raise ValueError("Must provide json path or mongo url.")

        log.info("BarcodeDetector instantiated.")


    def insert_mongo(self, event):
        return self._db_colleciton.insertOne(event).inserted_id

    
    def insert_json(self, event):
        """

        """
        with open(self._output_json_path, 'w', newline='', encoding='utf8') as fp:
            json.dump(event, fp, ensure_ascii=False, indent=2)
        return True    

    
    def query_database(self, det_data):
        """

        """
        answers = []
        for det in det_data:
            answers.append(self.query(det['data']))
        return ansers


    def preprocess_frame(self, frame):
        """
        Take the gradients of the frame
        """
        
        image = cv2.imread(args["image"]) # read image from given path
        gray = cv2.cv2Color(image, cv2.COLOR_BGR2GRAY)

        ddepth = cv2.cv.CV_32F if imutils.is_cv2() else cv2.CV_32F
        gradX = cv2.Sobel(gray, ddpeth=ddepth, dx=1, dy=0, ksize=-1)
        gradY = cv2.Sobel(gray, ddepth=ddepth, dx=0, dy=1, ksize=-1)

        gradient = cv2.subtract(gradX, gradY)

        return gray


    def detect_and_decode(self, frame):
        """
        Return
        det_data = [{"type": code, "codeType": code type, "polygon": location}]
        """
        decoded_objects = pyzbar.decode(frame)
        decoded_list = []
        for obj in decoded_objects:
            decoded_dict = {"type":obj.type, "data": obj.data.decode('utf-8'), "polygon": obj.polygon, "rectangle":obj.rect, 'string_data':str(obj.data)}
            decoded_list.append(decoded_dict)
        return decoded_list


    def draw_detections_bbox(self, frame, detections):
        """
        Draw codes on display

        Arguments:
            frame       : frame to be drawn on
            detections  : list with detection data

        Return:
            frame       : Frame drawn on
        """

        for obj in detections:
            points = obj["polygon"]

            # If the points do not form a quad, find convex hull
            if len(points) > 4: 
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else: 
                hull = points
            
            # Number of points in the convex hull
            n = len(hull)
        
            # Draw the convext hull
            for j in range(0,n):
                cv2.line(frame, hull[j], hull[ (j+1) % n], (255,0,0), 3)
        
        return frame

    
    def draw_detections_info(self, canvas, det_data):
        """
        Draw deteciton info on the frame.
        """
        font                   = cv2.FONT_HERSHEY_SIMPLEX
        fontScale              = 1
        fontColor              = (127,255,0)
        lineType               = 2
        color                  = (255,0,0)
        for det in det_data:
            # bottomLeftCorvner = (det['polygon'][0][0], det['polygon'][0][1])
            cv2.putText(canvas,
                        str(det['data']),
                        (det['polygon'][0][0]-100, det['polygon'][0][1]),
                        font,
                        fontScale,
                        color,
                        lineType)

        return canvas


    def handle_code(self, code): # TODO: Finish
        """
        Since this module detects different types of codes, parse them and send them to the 
        appropriate methods.

        This funciton calls the query funciton.

        """
        if code['type'] == 'QRCODE':
            pass
        elif code['type'] == 'Code128':
            pass
        elif code['type'] == 'Code93':
            pass
        elif code['type'] == 'Code39':
            pass
        elif code['type'] == 'Interleaved2of5':
            pass
    

    def load_camera(self):
        self._video_cap = cv2.VideoCapture(0)
        self._video_info = {}
        self._video_info['frame_height'] = self._video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self._video_info['frame_width'] = self._video_cap.get(cv2.CAP_PROP_FRAME_WIDTH)


    def run(self):
        """t
        Run main loop. The concept is to continuously run the camera, select random frame to process (10%)
        """
        self.load_camera()

        # FPS counter
        start_time = time.time()
        seconds = 5
        counter = 0
        fps = 0

        sleep = [False, time.time()]

        ret, frame = self._video_cap.read()
        canvas = np.zeros_like(frame)

        log.info("Running main loop.")
        while True:

            if random.random() < self._perc_to_process:
                # frame = self.preprocess_frame(frame)
                if not sleep[0]:
                    det_data = self.detect_and_decode(frame)
                    
                    if len(det_data) > 0:
                        log.info("Barcode detected. Type: {}. Data: {}".format(det_data[0]['type'], det_data[0]['data']))
                        frame = self.draw_detections_bbox(frame, det_data)
                        canvas = self.draw_detections_info(canvas, det_data)
                        sleep = [True, time.time()]

                        # TODO: Query the DB with the detected codes.
                        for det in det_data:
                            res = self.handle_code(det)
                            

                if (time.time() - sleep[1]) > self._sleep_detection:
                    sleep[0] = False
                    canvas = np.zeros_like(frame)
                
            
            # show frame
            img = cv2.add(frame, canvas)
            cv2.imshow("Barcode Detector", img)

            # Cap next frame
            ret, frame = self._video_cap.read()

            # Quit
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                print("\n\nINFO - Quit video")
                break
            
            # FPS
            counter += 1
            if (time.time()-start_time) > seconds:
                fps =  counter/(time.time()-start_time)
                counter = 0
                start_time = time.time()
                print("FPS: ", fps)
    
        cv2.destroyAllWindows()

        
if __name__=="__main__":
    output_json_path = './data/detections.json'
    perc_to_process = 1.0
    
    detector = BarcodeDetector(perc_to_process, output_json_path=output_json_path)
    detector.run()