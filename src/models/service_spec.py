import json

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, List, Optional

from models.action_type import ActionType

class ServiceSpecCharacteristicValueAndAlias(BaseModel):
    value: Optional[str] = None
    alias: Optional[str] = None

    @classmethod
    def from_string(cls, value: str) -> "ServiceSpecCharacteristicValueAndAlias":
        try:
            json_value = json.loads(value)
            if isinstance(json_value, dict):
                return cls(**json_value)
        except ValueError:
            pass
        return cls(value=value)

    def __json__(self) -> dict:
        return {
            "value": self.value,
            "alias": self.alias
        }

    def __eq__(self, other) -> bool:
        if not isinstance(other, ServiceSpecCharacteristicValueAndAlias):
            return False
        if self.value is None and other.value is None:
            return True
        if self.value is None or other.value is None:
            return False
        return self.value == other.value and self.alias == other.alias

class ServiceSpecCharacteristicValue(BaseModel):
    value: Optional[ServiceSpecCharacteristicValueAndAlias] = None
    is_default: Optional[bool] = Field(alias="isDefault", default=None)
    value_type: Optional[str] = Field(alias="valueType", default=None)
    unit_of_measure: Optional[str] = Field(alias="unitOfMeasure", default=None)
    value_from: Optional[str] = Field(alias="valueFrom", default=None)
    value_to: Optional[str] = Field(alias="valueTo", default=None)

    @field_validator("value", mode="before")
    def _accept_single_string_as_value(cls, value):
        if isinstance(value, str):
            return ServiceSpecCharacteristicValueAndAlias.from_string(value)
        return value

    def __json__(self) -> Optional[dict]:
        return self.value.__json__() if self.value else None
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ServiceSpecCharacteristicValue):
            return False
        if self.value is None and other.value is None:
            return True
        if self.value is None or other.value is None:
            return False
        return self.value == other.value

class ServiceSpecCharacteristic(BaseModel):
    name: str
    description: Optional[str] = None
    configurable: Optional[bool] = None
    extensible: Optional[bool] = None
    value_type: Optional[str] = Field(alias="valueType", default=None)
    min_cardinality: Optional[int] = Field(alias="minCardinality", default=None)
    max_cardinality: Optional[int] = Field(alias="maxCardinality", default=None)
    service_spec_characteristic_value: List[ServiceSpecCharacteristicValue] = \
        Field(alias="serviceSpecCharacteristicValue")
    
    @model_validator(mode="before")
    def _validate_before(cls, service_spec_characteristic: "ServiceSpecCharacteristic") -> "ServiceSpecCharacteristic":
        service_spec_characteristic = cls._accept_service_spec_char_from_service_inventory(service_spec_characteristic)
        return cls._populate_value_from_and_value_to(service_spec_characteristic)

    @classmethod
    def _accept_service_spec_char_from_service_inventory(cls, service_spec_characteristic: "ServiceSpecCharacteristic") -> "ServiceSpecCharacteristic":
        if "value" not in service_spec_characteristic:
            return service_spec_characteristic
        service_spec_characteristic_values = service_spec_characteristic.get("value")
        if service_spec_characteristic_values:
            if not isinstance(service_spec_characteristic_values, list):
                service_spec_characteristic_values = ServiceSpecCharacteristic \
                    ._get_single_service_spec_characteristic_value_as_list(service_spec_characteristic_values)
            service_spec_characteristic["serviceSpecCharacteristicValue"] = service_spec_characteristic_values
        return service_spec_characteristic
    
    @classmethod
    def _populate_value_from_and_value_to(cls, service_spec_characteristic: "ServiceSpecCharacteristic") -> "ServiceSpecCharacteristic":
        value_from = None
        value_to = None
        for service_spec_characteristic_value in service_spec_characteristic.get("serviceSpecCharacteristicValue", []):
            if service_spec_characteristic_value.value.alias == "valueFrom":
                value_from = service_spec_characteristic_value.value.value
            elif service_spec_characteristic_value.value.alias == "valueTo":
                value_to = service_spec_characteristic_value.value.value
        for service_spec_characteristic_value in service_spec_characteristic.get("serviceSpecCharacteristicValue", []):
            if service_spec_characteristic_value.value.alias == "interval":
                service_spec_characteristic_value.value_from = value_from
                service_spec_characteristic_value.value_to = value_to
        return service_spec_characteristic

    def find_value_from_alias(self, alias: str) -> Optional[str]:
        for service_spec_char_value in self.service_spec_characteristic_value:
            if service_spec_char_value.value.alias == alias:
                return service_spec_char_value.value.value
        return None
    
    @classmethod
    def _get_single_service_spec_characteristic_value_as_list(
        cls,
        service_spec_characteristic_values: Any
    ) -> List[ServiceSpecCharacteristicValue]:
        service_spec_characteristic_value = service_spec_characteristic_values.get("value")
        service_spec_characteristic_alias = service_spec_characteristic_values.get("alias")
        if service_spec_characteristic_value is not None:
            try:
                return ServiceSpecCharacteristic._get_service_spec_characteristic_values_from_string(
                        service_spec_characteristic_value, 
                        service_spec_characteristic_alias
                    )
            except:
                pass
        return [
            ServiceSpecCharacteristicValue(value=ServiceSpecCharacteristicValueAndAlias(
                value=service_spec_characteristic_value,
                alias=service_spec_characteristic_alias
            ))
        ]

    @classmethod
    def _get_service_spec_characteristic_values_from_string(
        cls,
        service_spec_characteristic_value: str, 
        service_spec_characteristic_alias: str
    ) -> List[ServiceSpecCharacteristicValue]:
        service_spec_characteristic_value_json = json.loads(service_spec_characteristic_value)
        if isinstance(service_spec_characteristic_value_json, list):
            return [
                ServiceSpecCharacteristicValue(value=ServiceSpecCharacteristicValueAndAlias(**item)) 
                for item in service_spec_characteristic_value_json
            ]
        return [
            ServiceSpecCharacteristicValue(value=ServiceSpecCharacteristicValueAndAlias(
                value=str(service_spec_characteristic_value_json) 
                if service_spec_characteristic_value_json else None,
                alias=service_spec_characteristic_alias
            ))
        ]

    @field_validator("value_type", mode="before")
    def _upper_value_type(cls, value_type):
        if value_type is not None:
            return value_type.upper()
        return None

    def __json__(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "valueType": self.value_type,
            "configurable": self.configurable,
            "minCardinality": self.min_cardinality,
            "maxCardinality": self.max_cardinality,
            "extensible": self.extensible,
            "value": 
                json.dumps([value.__json__() for value in self.service_spec_characteristic_value]) \
                if len(self.service_spec_characteristic_value) > 1 \
                else self.service_spec_characteristic_value[0].__json__()
        }

class ServiceSpec(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = Field(alias="@type", default=None)
    service_spec_characteristic: Optional[List[ServiceSpecCharacteristic]] = \
        Field(alias="serviceSpecCharacteristic", default=[])
    
    def __json__(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "version": self.version
        }
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ServiceSpec):
            return False
        return self.name == other.name and self.id == other.id and self.version == other.version

class ServiceSpecWithAction(ServiceSpec):
    action: Optional[ActionType] = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, ServiceSpecWithAction):
            return False
        return super().__eq__(other) and self.action == other.action

    class Config:
        json_encoders = {
            "ServiceSpecWithAction": lambda obj: {
                "name": obj.name,
                "id": obj.id,
                "action": obj.action,
            }
        }
