from enum import StrEnum, auto


class TaskType(StrEnum):
    MULTI_LABEL = auto()
    MULTI_CLASS = auto()
