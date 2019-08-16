import copy
import random
import time
import json
import cv2
import sys
from math import sqrt
from pymongo import MongoClient

# Main class (Behavior) helpers.
class Queue(object):
    """
    Queue object with a push method that returns the popped object when the queue is full.

    """
    def __init__(self, max_len=200):
        self.queue = []
        self.max_len = max_len

    def push(self, element):
        if len(self.queue) > self.max_len:
            self.queue.append(element)
            return self.queue.pop(0)
        else:
            self.queue.append(element)
            return False


def calculate_coordinate(bound_box):
    """
    Recieves a bounding box and return the centroid of the bottom fourth segment.

    ARGUMENTS
    ---------
    bound_box : (x_min, y_min, x_max, y_max)
    
    RETURNS
    -------
    bottom_centroid : coordinates of the centroid corresponding to the bottom region (1/3)
                        of the detection bounding box.
    """
    x_min = bound_box[0]
    x_max = bound_box[2]
    y_max = bound_box[3]
    y_min = bound_box[1] + (((y_max-bound_box[1])*(2/3))) # y_min + 3/4*delta_y
    # cen_x = int((x_max-x_min)/2 + x_min)
    # cen_y = int((y_max-y_min)/2 + y_min)
    cen_x = (x_min+x_max)//2
    cen_y = (y_min+y_max)//2
    return (cen_x, cen_y)


def calculate_direction(first_point, second_point):
    """
    Returns the difference vector sec_point - first_point
    """
    return (second_point[0]-first_point[0], second_point[1]-first_point[1])


def is_entering_area(areas, first_coord, second_coord):
    """
    Checks if the second coordenate is inside a region and if the first is outside of it.
    If a person is entering an area, he/she is leaving the scene, so the detection will be added to the "out" area id

    ARGUMENTS:
        first_coord     :
        second coord    :
    """

    for area_id in areas.keys():
        area = areas[area_id]

        if area["flux"] == "out": # People entering this area are leaving the scene
            is_first_in = cv2.pointPolygonTest(area["contour"], first_coord, False)
            
            is_second_in = cv2.pointPolygonTest(area["contour"], second_coord, False)
            
            if (is_first_in==-1) and (is_second_in==1):
                # print("Is first in: {}, is second in: {}".format(is_first_in, is_second_in))
                return area_id
    else:
        return False


def is_exiting_area(areas, first_coord, second_coord): 
    """
    Checks if second first coordenate is inside a region and if the first coordenate is outside of it.
    If a person is leaving an area, he/she is entering the scene, so the detection will be added to the "in" area id

    ARGUMENTS:
        first_coord     :
        second coord    :
    """
    for area_id in areas.keys():
        area = areas[area_id]

        if area["flux"] == "in": # People leaving this area is entering the scene         
            is_first_in = cv2.pointPolygonTest(area["contour"], first_coord, False)
            is_second_in = cv2.pointPolygonTest(area["contour"], second_coord, False)
            
            if (is_first_in==1) and (is_second_in==-1):
                
                return area_id
    else:
        return False


# ------------------------------------------------------------------------------------------------
# Areas
def generateID(ids_list):
    """
    Create a random and unique numerical id from 00000 to 99999.

    ARGUMENTS
    ---------
    ids_list    : list with ids already in use.

    """
    while True:
        id_ = '{:05}'.format(random.randrange(1, 10**5))
        if id_ not in ids_list:
            ids_list.append(id_)
            return id_
    

def generateAreas(areas):
    """
    Generates and return a dictionary containing areas data

    ARGUMENTS
    ---------
    regions = [
                ar_0 = {"contour": np.array([[35,322], [35,245], [95,222], [140,460], [104,470]], dtype=np.int32),
                        "type": "loja"}
                ar_1 = {"contour": np.array([[72,118], [90,115], [105,222], [88,212]], dtype=np.int32),
                        "type": "corredor"}
                ar_2 = {"contour": np.array([[255,30], [380,29], [367,111], [225,95]], dtype=np.int32),
                        "type": "corredor"}
                ar_3 = {"contour": np.array([[570,455], [702,322], [702,455]], dtype=np.int32),
                        "type": "corredor"}
                ar_4 = {"contour": np.array([[100,455], [720,455], [720,480], [100,480]], dtype=np.int32),
                        "type": "corredor"}
            
    RETURN
    ------
    final_areas: {"_id": {"area_id": "_id",
                            "contour": ,
                            "type": ,
                            "flux": 
                            },
                    }
    
    """
    
    print("INFO - utils.generateAreas called()")

    _ids_list = []
    final_areas = {}

    for area in areas:
        "in area"
        in_area = {}
        in_area["area_id"] = generateID(_ids_list) 
        in_area["contour"] = copy.deepcopy(area["contour"])
        in_area["type"] = copy.deepcopy(area["type"])
        in_area["flux"] = "in"
        final_areas[in_area["area_id"]] = copy.deepcopy(in_area)

        "out area"
        out_area = {}
        out_area["area_id"] = '{:05}'.format(int(in_area["area_id"])+1)
        out_area["contour"] = copy.deepcopy(area["contour"])
        out_area["type"] = copy.deepcopy(area["type"])
        out_area["flux"] = "out"
        final_areas[out_area["area_id"]] = copy.deepcopy(out_area)

        _ids_list.append(in_area["area_id"])
        _ids_list.append(out_area["area_id"])

    return final_areas


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def save_areas_to_json(areas, path):
    """
    Save areas to a json file.

    """
    # path = 'areas/areas.json'
    # Jsonfy numpy array

    with open(path, 'w', newline='', encoding='utf8') as fp:
        json.dump(areas, fp, ensure_ascii=False, indent=2, default=str, cls=NumpyEncoder)


def load_areas_from_json(areas_path):
    """
    Recieve a path to a json file, where areas are stored.
    Return the dictionary, converting the areas[_id]['contour'] attribute to a numpy array.

    """
    with open(areas_path, 'r', newline='', encoding='utf8') as fp:
        areas = json.loads(fp)
        fp.close()

    # Unjsonfy
    for _id in areas.keys():
        areas[_id]['contour'] = np.array(areas[_id]['contour'])
    return areas


def get_areas(camera_name):
    """
    This function is called by the Behavior component, as it is instantiated.
    The camera name should have been passed through the front application (flow design)
    Areas will be stored in the folder ../../data/areas/, as a json file.
    """
    if 'DATA_PATH' in os.environ.keys():
        areas_file = camera_name + "_areas.json"
        areas_path = os.path.join(os.environ['DATA_PATH'], 'areas', areas_file)
        if os.path.isfile(ares_file):
            return load_areas_from_json(areas_path)
        else:
            raise Exception("No areas file found.")
    else:
        raise Exception('Must have environment DATA_PATH')


def draw_areas(frame, areas):
    """
    Draw the areas and their ids on the frmae.

    ARGUMENTS
    ---------
    frame   : opencv array (numpy)
    areas   : dictionary, where key are areas ids

    RETURN
    ------
    frame   : oepncv array (numpy) drawn on.

    """
    font                   = cv2.FONT_HERSHEY_SIMPLEX
    fontScale              = 0.5
    fontColor              = (127,255,0)
    lineType               = 2

    num_areas = 0
    for area in areas.keys():
        if areas[area]["flux"] == "in":
            num_areas += 1
            M = cv2.moments(areas[area]["contour"])
            cX = int(M["m10"]/M["m00"])
            cY = int(M["m01"]/M["m00"])
            bottomLeftCornerOfText = (cX-5, cY+5)
            cv2.putText(frame, 
                        str(areas[area]["area_id"]),
                        bottomLeftCornerOfText,
                        font,
                        fontScale,
                        fontColor,
                        lineType)
            cv2.drawContours(frame, [areas[area]["contour"]], 0, (0,0,0), 2)

    # print("{} areas were drawn.".format(num_areas))
    return frame


def show(areas, image_path):
    """
    Display the image from the path continuously with areas drawn on it.

    """
    image = cv2.imread(image_path)
    image = draw_areas(image, areas)
    while True:   
        cv2.imshow('Areas 15', image)
        # Quit
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            print("INFO - Quit video")
            break
    cv2.destroyAllWindows()


def save_areas_and_image(areas):
    """
    Save areas to a json file and draw the areas on a copy of a frame image.

    """
    #saving json
    path = 'areas/areas.json'
    with open(path, 'w', newline='', encoding='utf8') as fp:
        json.dump(areas, fp, ensure_ascii=False, indent=2, default=str)

    # Saving image
    image_path = "areas/90channel15.jpg"
    image = cv2.imread(image_path)
    image = draw_areas(image, areas)
    cv2.imwrite("areas/90channel15_withAreas.jpg", image)

        
# ---------------------------------------------------------------------------------------------
# OTHERS
def calculate_distance(first_coord, second_coord):
        return sqrt((second_coord[0]-first_coord[0])**2+(second_coord[1]-first_coord[1])**2)


def draw_ids_if_far(first_coord, second_coord, threshold, frame, _id, color, frame_i):
    """
    Checks if the distance between the coordenates is larger than a threshold. If so, 
    draws the ids on top of the detection.
    This means that the trackin isn't working, since two consecutives coordenates can't be this far apart.
    """
    
    if calculate_distance(first_coord, second_coord) > threshold:
        
        font                   = cv2.FONT_HERSHEY_SIMPLEX
        fontScale              = 0.5
        fontColor              = (127,255,0)
        lineType               = 2
        
        bottomLeftCornerAB = (first_coord[0]-100, first_coord[1]-100+random.randint(-10,10))
        bottomLeftCornerCD = (second_coord[0]-100, second_coord[1]-100+random.randint(-10,10))
        
        cv2.putText(frame, 
                        "NEW"+_id,
                        bottomLeftCornerAB,
                        font,
                        fontScale,
                        color,
                        lineType)

        
        cv2.putText(frame, 
                        "OLD"+_id,
                        bottomLeftCornerCD,
                        font,
                        fontScale,
                        color,
                        lineType)  

        frame = cv2.circle(frame, (640, 365), 20, [255, 0, 0], -1)
        # print("Frame should be drawn on.", frame_i)
        # time.sleep(1.5)
        return frame, True

    else:
        return frame, False


def putText(frame, text, bottomLeftCorner, color=(255,255,255)):

    font                   = cv2.FONT_HERSHEY_SIMPLEX
    fontScale              = 0.5
    lineType               = 2
    
    cv2.putText(frame,
                text,
                bottomLeftCorner,
                font,
                fontScale,
                color,
                lineType)
    
    return frame


def draw_bbox_coords(bound_box, frame):
    x_min = bound_box[0]
    y_min = bound_box[1]
    x_max = bound_box[2]
    y_max = bound_box[3]
    framne = putText(frame, 'x_min', x_min)
    framne = putText(frame, 'y_min', y_min)
    framne = putText(frame, 'x_max', x_max)
    framne = putText(frame, 'y_max', y_max)
    return frame