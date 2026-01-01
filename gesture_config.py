from enums import FingerLM, ALL_FINGERS

single_finger_to_gesture = {
    {finger} : f"only-{finger.name.lower()}"
        for finger in ALL_FINGERS
}

down_fingers_to_gesture = {
    **single_finger_to_gesture,
    set(): "fist",
    set(ALL_FINGERS): "all-up",
    {FingerLM.INDEX, FingerLM.PINKY}: "spiderman",
    {FingerLM.INDEX, FingerLM.MIDDLE}: "peace-sign",
}
