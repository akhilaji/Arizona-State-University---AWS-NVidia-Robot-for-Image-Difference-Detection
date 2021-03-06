from skeleton.detect import BoundingBox, ID, ObjectDetection

import collections
import itertools

from cv2 import cv2
import numpy as np

from typing import Any, Callable, Dict, Iterator, Iterable, List, Mapping, NamedTuple, Tuple, TypeVar, Set
from nptyping import NDArray

Centroid = NDArray[2, np.float32]

def centroid(bbox: BoundingBox) -> Centroid:
    return np.array([bbox.x + bbox.w / 2.0, bbox.y + bbox.h / 2.0], np.float32)

def centroid_distance(c1: Centroid, c2: Centroid) -> float:
    return np.sqrt((c2[1] - c1[1]) ** 2.0 + (c2[0] - c1[0]) ** 2.0)

def pos_kalman_filter(centroid: Centroid, p_noise_cov_scale: float = 0.03) -> cv2.KalmanFilter:
    k_filter = cv2.KalmanFilter(4, 2)
    k_filter.measurementMatrix  = np.array([[1, 0, 0, 0],
                                            [0, 1, 0, 0]], np.float32)

    k_filter.transitionMatrix   = np.array([[1, 0, 1, 0],
                                            [0, 1, 0, 1],
                                            [0, 0, 1, 0],
                                            [0, 0, 0, 1]], np.float32)

    k_filter.processNoiseCov    = np.array([[1, 0, 0, 0],
                                            [0, 1, 0, 0],
                                            [0, 0, 1, 0],
                                            [0, 0, 0, 1]], np.float32) * p_noise_cov_scale

    k_filter.statePost = np.array([[centroid[0]],
                                   [centroid[1]],
                                   [0.0],
                                   [0.0]], np.float32)

    k_filter.statePre  = np.array([[centroid[0]],
                                   [centroid[1]],
                                   [0.0],
                                   [0.0]], np.float32)

    return k_filter

class ObjectTracker:
    """
    Abstract callable object to run object tracking on the detected object
    instances found in sequential frames from a video feed. Does this by
    assigning an id to each detected object instance. Implementation details to
    be specified by implementation sof this interface.
    """

    def __call__(self, detections: List[ObjectDetection]) -> None:
        """
        Assigns ids to each of the detected object instances.
        """
        pass

class CentroidTracker:

    class ObjectInstance:
        def __init__(self,
                kfilter: cv2.KalmanFilter,
                detection: ObjectDetection = None,
                age: int = 0,
            ):
            self.kfilter = kfilter
            self.detection = detection
            self.age = age

        def correct(self, measurement: Centroid) -> None:
            self.kfilter.correct(np.reshape(measurement, (2, 1)))
        
        def predict(self) -> Centroid:
            pos_x, pos_y, vel_x, vel_y = self.kfilter.predict()
            return np.array([*pos_x, *pos_y], np.float32)

    def __init__(self,
            on_screen: Set[ID] = set(),
            off_screen: Set[ID] = set(),
            id_itr: Iterator[ID] = itertools.count(start=0, step=1),
            dist_f: Callable[[Centroid, Centroid], float] = centroid_distance,
            kfilter_factory: Callable[[], cv2.KalmanFilter] = pos_kalman_filter,
            pruning_age: int = 50,
            dist_thresh: float = 500.0,
        ):
        self.on_screen = on_screen
        self.off_screen = off_screen
        self.id_itr = id_itr
        self.dist_f = dist_f
        self.kfilter_factory = kfilter_factory
        self.obj_instance = dict()
        self.pruning_age = pruning_age
        self.dist_thresh = dist_thresh
    
    def __call__(self, detections: List[ObjectDetection]) -> None:
        c_pred = {o_id: o_inst.predict() for o_id, o_inst in self.obj_instance.items()}  
        def closest_detection(o_ids: Iterable[ID]) -> Tuple[ID, ObjectDetection]:
            closest_o_id, closest_det = None, None
            min_dist = self.dist_thresh
            for o_id in o_ids:
                o_id_class = self.obj_instance[o_id].detection.obj_class
                valid_match = lambda x: x.id == None and x.obj_class == o_id_class
                for det in filter(valid_match, detections):
                    alt_dist = self.dist_f(c_pred[o_id], centroid(det.bbox))
                    if alt_dist < min_dist:
                        closest_o_id, closest_det = o_id, det
                        min_dist = alt_dist
            return closest_o_id, closest_det
        def assign_id(o_id: ID, det: ObjectDetection) -> None:
            measurement = centroid(det.bbox)
            if o_id not in self.obj_instance:
                self.obj_instance[o_id] = self.ObjectInstance(self.kfilter_factory(measurement))
            o_inst = self.obj_instance[o_id]
            o_inst.correct(measurement)
            o_inst.detection = det
            o_inst.age = 0
            det.id = o_id
        while self.on_screen:
            o_id, det = closest_detection(self.on_screen)
            if o_id == None:
                break
            else:
                assign_id(o_id, det)
                self.on_screen.remove(o_id)
        while self.off_screen:
            o_id, det = closest_detection(self.off_screen)
            if o_id == None:
                break
            else:
                assign_id(o_id, det)
                self.off_screen.remove(o_id)
        for det in filter(lambda x: x.id == None, detections):
            assign_id(next(self.id_itr), det)
        for o_inst in self.obj_instance.values():
            o_inst.age += 1
        to_remove = [o_id for o_id, o_inst in self.obj_instance.items() if o_inst.age > self.pruning_age]
        for o_id in to_remove:
            del self.obj_instance[o_id]
        self.on_screen = {det.id for det in detections}
        self.off_screen = self.obj_instance.keys() - self.on_screen
