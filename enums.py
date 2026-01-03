from enum import Enum, IntEnum

class FingerLM(IntEnum):
    THUMB = 4
    INDEX = 8
    MIDDLE = 12
    RING = 16
    PINKY = 20
    ROOT_POSITION = 0
    DIST_REF_POSITION = 1

ALL_FINGERS = tuple(sorted([FingerLM.THUMB, FingerLM.INDEX, FingerLM.MIDDLE, FingerLM.RING, FingerLM.PINKY]))

class ThumbLM(IntEnum):
    CMC = 1 # CMC
    MCP = 2
    IP = 3
    TIP = 4

THUMB_LMS = tuple(sorted([ThumbLM.CMC, ThumbLM.MCP, ThumbLM.IP, ThumbLM.TIP]))

class Command(Enum):
    NULL = (-1, None)
    BL_ON = (0, True)
    BL_OFF = (0, False)
    GL_ON = (1, True)
    GL_OFF = (1, False)
    GD_ON = (2, True)
    GD_OFF = (2, False)
