from enum import Enum

class FingerLM(Enum):
    THUMB = 4
    INDEX = 8
    MIDDLE = 12
    RING = 16
    PINKY = 20
    ROOT_POSITION = 0

ALL_FINGERS = [FingerLM.THUMB, FingerLM.INDEX, FingerLM.MIDDLE, FingerLM.RING, FingerLM.PINKY]

class Command(Enum):
    BL_ON = (0, True)
    BL_OFF = (0, False)
    GL_ON = (1, True)
    GL_OFF = (1, False)
    GD_ON = (2, True)
    GD_OFF = (2, False)
