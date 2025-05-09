import json
import random

from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Tuple

from models.service_order import ServiceOrder
from models.service_spec import ServiceSpecCharacteristic, ServiceSpecCharacteristicValue, ServiceSpecCharacteristicValueAndAlias
from models.service_spec_char_value_handler import ServiceSpecCharValueHandler

class MtdIntervalType(str, Enum):
    MINIMUM = "min"
    MAXIMUM = "max"
    RANDOM = "random"
    INACTIVE = "inactive"

class MtdIntervalStrategy(ABC):
    _minimum: int
    _maximum: int

    def __init__(self, minimum: int, maximum: int):
        self._minimum = minimum
        self._maximum = maximum

    @classmethod
    def create(cls, mtd_interval_type: MtdIntervalType, minimum: int, maximum: int) -> "MtdIntervalStrategy":
        if mtd_interval_type == MtdIntervalType.MINIMUM:
            return MinimumMtdIntervalStrategy(minimum, maximum)
        if mtd_interval_type == MtdIntervalType.MAXIMUM:
            return MaximumMtdIntervalStrategy(minimum, maximum)
        if mtd_interval_type == MtdIntervalType.RANDOM:
            return RandomMtdIntervalStrategy(minimum, maximum)
        return InactiveMtdIntervalStrategy(minimum, maximum)

    @abstractmethod
    def get_interval(self) -> int:
        pass

class MinimumMtdIntervalStrategy(MtdIntervalStrategy):
    def get_interval(self) -> int:
        return self._minimum
    
class MaximumMtdIntervalStrategy(MtdIntervalStrategy):
    def get_interval(self) -> int:
        return self._maximum
    
class RandomMtdIntervalStrategy(MtdIntervalStrategy):
    def get_interval(self) -> int:
        return random.randint(self._minimum, self._maximum)
    
class InactiveMtdIntervalStrategy(MtdIntervalStrategy):
    def get_interval(self) -> int:
        return 0

class MtdAction(BaseModel):
    order_item: int
    service_spec_char_name: str
    service_spec_char_values: ServiceSpecCharValueHandler
    interval: int
    time_until_mutation: int
    interval_type: MtdIntervalType

    @classmethod
    def from_service_order(cls, service_order: ServiceOrder, previous_mtd_actions: List["MtdAction"], mtd_tag_lowercase: str = "mutation::") \
    -> List["MtdAction"]:
        mtd_actions = []
        for order_item_index, order_item in enumerate(service_order.order_items):
            for service_char in order_item.service.service_chars:
                if not service_char.name.lower().startswith(mtd_tag_lowercase):
                    continue
                service_char_split = service_char.name.split("::")
                if len(service_char_split) < 2:
                    continue
                attribute_name = service_char_split[-1]
                possible_values, interval, interval_type = \
                    cls._parse_values_and_interval_from_service_spec_characteristic(attribute_name, service_char, previous_mtd_actions)
                if possible_values and interval != 0:
                    cls._add_mtd_action_to_list(possible_values, order_item_index, attribute_name, interval, interval_type, mtd_actions)
        return mtd_actions

    @classmethod
    def _parse_values_and_interval_from_service_spec_characteristic(
        cls, 
        attribute_name: str, 
        service_spec_characteristic: ServiceSpecCharacteristic, 
        previous_mtd_actions: List["MtdAction"]
    ) -> Tuple[str, int, MtdIntervalType]:
        possible_values = None
        interval = 0
        interval_type = None
        for service_char_value in service_spec_characteristic.service_spec_characteristic_value:
            if not service_char_value.value.alias:
                possible_values = service_char_value.value.value
            elif service_char_value.value.alias == "interval":
                interval_type = service_char_value.value.value
                update = not [previous_mtd_action for previous_mtd_action in previous_mtd_actions 
                              if previous_mtd_action.service_spec_char_name == attribute_name and previous_mtd_action.interval_type == interval_type]
                if update:
                    try:
                        minimum_interval = int(service_char_value.value_from)
                        maximum_interval = int(service_char_value.value_to)
                        interval = MtdIntervalStrategy.create(MtdIntervalType(interval_type), minimum_interval, maximum_interval).get_interval()
                    except:
                        continue
        return (possible_values, interval, interval_type)

    @classmethod
    def _add_mtd_action_to_list(
        cls, 
        possible_values: str, 
        order_item: int, 
        attribute_name: str, 
        interval: int, 
        interval_type: MtdIntervalType, 
        mtd_actions: List["MtdAction"]
    ):
        values = ServiceSpecCharValueHandler.from_json(possible_values)
        if values:
            try:
                mtd_actions.append(MtdAction(
                    order_item=order_item,
                    service_spec_char_name=attribute_name,
                    service_spec_char_values=values,
                    interval=interval,
                    time_until_mutation=interval,
                    interval_type=interval_type
                ))
            except json.JSONDecodeError as json_error:
                print(f"Error decoding JSON: {json_error}")
            except ValueError as value_error:
                print(f"Error: {value_error}")

    def decrement_time_and_get_service_spec_characteristic_if_zero(self) -> Optional[ServiceSpecCharacteristic]:
        if self.time_until_mutation == 0:
            self.time_until_mutation = self.interval
            return ServiceSpecCharacteristic(
                name=self.service_spec_char_name,
                serviceSpecCharacteristicValue=[
                    ServiceSpecCharacteristicValue(
                        value=ServiceSpecCharacteristicValueAndAlias.from_string(
                            self.service_spec_char_values.get_random()
                        )
                    )
                ]
            )
        self.time_until_mutation = max(0, self.time_until_mutation - 1)
        return None
