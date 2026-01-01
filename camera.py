from iot_control import IOTConnection
import cv2
from enum import Enum

import mediapipe as mp

import math

class Finger(Enum):
    THUMB = 4
    INDEX = 8
    MIDDLE = 12
    RING = 16
    PINKY = 20

finger_id_map = {s: enum.value for s, enum in Finger._member_map_.items()}

ALL_FINGERS = [Finger.THUMB, Finger.INDEX, Finger.MIDDLE, Finger.RING, Finger.PINKY]

ROOT_POSITION = 0

class Command(Enum):
    BL_ON = (0, True)
    BL_OFF = (0, False)
    GL_ON = (1, True)
    GL_OFF = (1, False)
    GD_ON = (2, True)
    GD_OFF = (2, False)

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
        self.command = None
        self.prev_command = None
        self.curr_lm_state = ""
        self.prev_lm_state = ""
        self.lm0_x = None
        self.lm0_y = None

    def _hand_finder(self, image, draw=True):
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for landmark in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(image, landmark, self.mp_hands.HAND_CONNECTIONS)
        return image

    def _position_finder(self, image, hand_idx=0, draw=True):
        self.lm_list = []
        if self.results.multi_hand_landmarks:
            hand = self.results.multi_hand_landmarks[hand_idx]
            for id, lm in enumerate(hand.landmark):
                h, w, _ = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([id, cx, cy, lm.x, lm.y])

                if id == 0 and draw:
                    self.lm0_x = lm.x
                    self.lm0_y = lm.y
                    cv2.circle(image, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

    def _get_finger_dist(self, id):
        '''
        4 -- Thumb
        8 -- index
        12 -- Middle
        16 -- Ring
        20 -- Pinky
        '''
        if self.lm0_x is None or self.lm0_y is None: return None
        for lm in self.lm_list:
            if lm[0] == id: return math.sqrt((lm[3] - self.lm0_x)**2 +(lm[4] - self.lm0_y)**2)
        return None

    def _loop_print_state(self):
        self.curr_lm_state = self._print_and_return_state()
        if self.curr_lm_state != self.prev_lm_state:
            self.prev_lm_state = self.curr_lm_state
            print(self.curr_lm_state)

    def _print_and_return_state(self):
        if len(self.curr_lm_state) == 0: return ""
        state = ""
        for finger, id in finger_id_map.items():
            finger_dist = self._get_finger_dist(id)
            if finger_dist is None: continue
            finger_lm_description = f"{finger}: {finger_dist}\n"
            state += finger_lm_description
        return state

    def _print_state(self):
        printed = False

        for finger, id in finger_id_map.items():
            finger_dist = self._get_finger_dist(id)
            if finger_dist is None: continue
            if not printed: printed = True
            print(f"{finger}: {finger_dist}")
            
        if printed: print()

    def _finger_down(self, fingers=[]):
        heights = []
        for finger in fingers:
            if finger == Finger.THUMB:
                heights.append(abs(self.lm_list[finger.value][2] - self.lm_list[ROOT_POSITION][2] < 100))
            else:   # The other fingers
                heights.append(abs(self.lm_list[finger.value][2] - self.lm_list[ROOT_POSITION][2] < 90))
        return heights

    def _check_are_fingers_up_others_down(self, target_fingers, heights_thres):
        assert len(target_fingers) == len(heights_thres), "target_fingers and heights_thres have diff lengths in _check_are_fingers_up_others_down()" 

        for idx, finger in enumerate(target_fingers):
            is_finger_up = abs(self.lm_list[finger.value][2] - self.lm_list[ROOT_POSITION][2]) >= heights_thres[idx]
            if not is_finger_up: return False

        other_fingers = [finger for finger in ALL_FINGERS if finger not in target_fingers]
        other_fingers_down = all(self._finger_down(fingers=other_fingers))

        return other_fingers_down

    def _gesture_command(self):
        if not self.lm_list: return

        # Only the index finger is up.
        if self._check_are_fingers_up_others_down([Finger.INDEX], [150]):
            print("Bedroom Light ON")
            self.command = Command.BL_ON

        # All fingers are down.
        if self._check_are_fingers_up_others_down([], []):
            print("Bedroom Light OFF")
            self.command = Command.BL_OFF

        # The index and middle fingers are up
        if self._check_are_fingers_up_others_down([Finger.INDEX, Finger.MIDDLE], [150, 200]):
            print("Garage Light ON")
            self.command = Command.GL_ON

        # Only the pinky finger is up
        if self._check_are_fingers_up_others_down([Finger.PINKY], [135]):
            print("Garage Light OFF")
            self.command = Command.GL_OFF

        # Thumbs-up gesture
        if self._check_are_fingers_up_others_down([Finger.THUMB], [100]):
            print("Opening Garage Door")
            self.command = Command.GD_ON

        # Rock hand sign
        if self._check_are_fingers_up_others_down([Finger.INDEX, Finger.PINKY], [150, 135]):
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

    def test(self, show=True):
        cap = cv2.VideoCapture(0)

        while True:
            success, frame = cap.read()

            if not success: break

            frame = self._hand_finder(frame)
            self._position_finder(frame)
            # self._loop_print_state()
            self._print_state()

            if show: cv2.imshow("Hand Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"): break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    tracker = HandGestureTracker()
    # tracker.run()
    tracker.test()

