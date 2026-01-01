from enums import FingerLM, ALL_FINGERS

def get_single_finger_up_gesture_name(finger):
    return f"only-{finger.name.lower()}-up"

single_finger_up_to_gesture = {
    (finger,) : get_single_finger_up_gesture_name(finger)
        for finger in ALL_FINGERS
}

up_fingers_to_gesture = {
    **single_finger_up_to_gesture,
    tuple(): "fist",
    ALL_FINGERS: "all-up",
    tuple(sorted([FingerLM.INDEX, FingerLM.PINKY])): "spiderman",
    tuple(sorted([FingerLM.INDEX, FingerLM.MIDDLE])): "peace-sign",
}
