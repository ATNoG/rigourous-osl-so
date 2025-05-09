from enum import Enum

class ActionType(str, Enum):
    DEPLOY = "DEPLOY"
    UPDATE = "UPDATE"
    REMOVE = "REMOVE"
