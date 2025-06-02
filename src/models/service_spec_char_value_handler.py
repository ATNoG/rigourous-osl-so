import json
import random

from pydantic import BaseModel, Field
from typing import List, Optional

class ValueRange(BaseModel):
    start: str
    end: Optional[str] = None

    @classmethod
    def from_string(cls, value: str, delimiter: str = "-") -> "ValueRange":
        split_value = value.split(delimiter)
        if len(split_value) == 2:
            try:
                start_value = int(split_value[0])
                end_value = int(split_value[1])
                if end_value > start_value:
                    return ValueRange(start=str(start_value), end=str(end_value))
            except:
                pass
        return ValueRange(start=value)
    
    def get_value(self, index: int = 0) -> str:
        if self.end is None or abs(index) > len(self):
            return self.start
        if index >= 0:
            return str(int(self.start) + index)
        return str(int(self.end) + index + 1)
    
    def __len__(self) -> int:
        return (int(self.end) - int(self.start) + 1) if self.end is not None else 1

class ServiceSpecCharValueHandler(BaseModel):
    list_of_values: List['ValueRange'] = Field(default_factory=list)

    @classmethod
    def from_json(cls, values: str) -> Optional["ServiceSpecCharValueHandler"]:
        value_list = []
        try:
            value_list = cls._get_value_ranges_from_json(values)
        except json.JSONDecodeError:
            pass
        return cls(list_of_values=value_list) if value_list else None
    
    @classmethod
    def _get_value_ranges_from_json(cls, values: str) -> List[ValueRange]:
        value_list = []
        json_values = json.loads(values)
        for value in json_values:
            if isinstance(value, str):
                value_list.append(ValueRange.from_string(value.strip()))
        return value_list

    def get_random(self) -> str:
        total_length = sum([len(values) for values in self.list_of_values])
        random_element = random.randint(0, total_length - 1)
        accumulator = 0
        for value in self.list_of_values:
            if random_element < accumulator + len(value):
                return value.get_value(random_element - accumulator)
            accumulator += len(value)
        return self.list_of_values[-1].get_value(-1)
