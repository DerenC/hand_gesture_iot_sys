from iot_control import IOTConnection
from enums import FingerLM, ALL_FINGERS, THUMB_LMS, Command
from utils import dist_between, get_diff_vec, get_angle
from constants import REF_BASED_RATIOS, THUMB_ANGLE_THRES
from gesture_config import up_fingers_to_gesture

import cv2

import mediapipe as mp

class HandGestureTracker(IOTConnection):

    def __init__(
            self,
            mode=False,
            max_hands=2,
            detection_conf=0.5,
            model_complexity=1,
            track_conf=0.5
        ):
        super().__init__()
        self.mode = mode
        self.max_hands = max_hands
        self.detection_conf = detection_conf
        self.model_complexity = model_complexity
        self.track_conf = track_conf
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(self.mode, self.max_hands, self.model_complexity, self.detection_conf, self.track_conf)
        self.mp_draw = mp.solutions.drawing_utils
        self.command = Command.NULL
        self.prev_command = Command.NULL
        self.lm0_xy = None
        self.lm1_xy = None
        self.ref_dist = None

    def _hand_finder(self, image, draw=True):
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for landmark in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(image, landmark, self.mp_hands.HAND_CONNECTIONS)
        return image

    def _get_ref_dist(self):
        assert self.lm0_xy is not None and self.lm1_xy is not None, \
            "self.lm0_xy or self.lm1_xy is None when calling self._get_self_dist()"
        return dist_between(self.lm0_xy[0], self.lm0_xy[1], self.lm1_xy[0], self.lm1_xy[1])

    def _position_finder(self, image, hand_idx=0, draw=True):
        self.lm_list = []
        if self.results.multi_hand_landmarks:
            hand = self.results.multi_hand_landmarks[hand_idx]
            for id, lm in enumerate(hand.landmark):
                h, w, _ = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([id, cx, cy, lm.x, lm.y])

                if id == FingerLM.ROOT_POSITION.value:
                    self.lm0_xy = (lm.x, lm.y)
                    if draw: cv2.circle(image, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

                elif id == FingerLM.DIST_REF_POSITION.value:
                    self.lm1_xy = (lm.x, lm.y)

            if self.lm0_xy is not None and self.lm1_xy is not None:
                self.ref_dist = self._get_ref_dist()

    def _get_finger_dist(self, finger):
        finger_lm_x, finger_lm_y = self.lm_list[finger.value][3:5]
        return dist_between(self.lm0_xy[0], self.lm0_xy[1], finger_lm_x, finger_lm_y)

    def _get_total_angle_diff(self):
        thumb_vecs = [
            get_diff_vec(
                self.lm_list[0][3],
                self.lm_list[0][4],
                self.lm_list[thumb_lm.value][3],
                self.lm_list[thumb_lm.value][4]
            ) for thumb_lm in THUMB_LMS
        ]
        total_angle = 0
        n = len(thumb_vecs) - 1
        for i in range(n):
            total_angle += get_angle(
                thumb_vecs[i][0],
                thumb_vecs[i][1],
                thumb_vecs[i + 1][0],
                thumb_vecs[i + 1][1]
            )
        
        return total_angle

    def _is_finger_up(self, finger):
        assert finger in REF_BASED_RATIOS and self.ref_dist is not None and self.ref_dist != 0, \
            "finger not found in REF_BASED_RATIOS when calling self._is_finger_up()"
        if finger == FingerLM.THUMB:
            return self._get_total_angle_diff() < THUMB_ANGLE_THRES
        return self._get_finger_dist(finger) / self.ref_dist >= REF_BASED_RATIOS[finger]

    def _which_fingers_up(self):
        up_fingers = []
        for finger in ALL_FINGERS:
            if self._is_finger_up(finger): up_fingers.append(finger)
        return tuple(sorted(up_fingers))

    def _finger_down(self, fingers=[]):
        heights = []
        for finger in fingers:
            if finger == FingerLM.THUMB:
                heights.append(abs(self.lm_list[finger.value][2] - self.lm_list[FingerLM.ROOT_POSITION][2] < 100))
            else:   # The other fingers
                heights.append(abs(self.lm_list[finger.value][2] - self.lm_list[FingerLM.ROOT_POSITION][2] < 90))
        return heights

    def _check_are_fingers_up_others_down(self, target_fingers, heights_thres):
        assert len(target_fingers) == len(heights_thres), "target_fingers and heights_thres have diff lengths in _check_are_fingers_up_others_down()" 

        for idx, finger in enumerate(target_fingers):
            is_finger_up = abs(self.lm_list[finger.value][2] - self.lm_list[FingerLM.ROOT_POSITION][2]) >= heights_thres[idx]
            if not is_finger_up: return False

        other_fingers = [finger for finger in ALL_FINGERS if finger not in target_fingers]
        other_fingers_down = all(self._finger_down(fingers=other_fingers))

        return other_fingers_down

    def _gesture_command(self):
        if not self.lm_list or self.lm0_xy is None or self.lm1_xy is None or self.ref_dist is None: return

        up_fingers = self._which_fingers_up()
        gesture_name = up_fingers_to_gesture.get(up_fingers, "")

        match gesture_name:

            case "only-index-up":
                print("Bedroom Light ON")
                self.command = Command.BL_ON

            case "fist":
                print("Bedroom Light OFF")
                self.command = Command.BL_OFF

            case "peace-sign":
                print("Garage Light ON")
                self.command = Command.GL_ON

            case "only-pinky-up":
                print("Garage Light OFF")
                self.command = Command.GL_OFF

            case "only-thumb-up":
                print("Opening Garage Door")
                self.command = Command.GD_ON

            case "spiderman":
                print("Closing Garage Door")
                self.command = Command.GD_OFF

        if self.command != self.prev_command:
            self.prev_command = self.command
            # send the message to broker
            self._send_to_topic(self.command.name)

    def run(self, show=True):
        cap = cv2.VideoCapture(0)

        while True:
            success, frame = cap.read()

            if not success: break

            frame = self._hand_finder(frame)
            self._position_finder(frame)
            self._gesture_command()

            if show: cv2.imshow("Hand Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"): break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    tracker = HandGestureTracker()
    tracker.run()
