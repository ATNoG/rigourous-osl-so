from pydantic import BaseModel, Field
from typing import List, Optional

from models.service_spec import ServiceSpec, ServiceSpecCharacteristic

class ServiceInventory(BaseModel):
    name: str
    uuid: str
    id: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = Field(alias="startDate", default=None)
    end_date: Optional[str] = Field(alias="endDate", default=None)
    state: Optional[str] = None
    service_order_id: Optional[str] = Field(alias="serviceOrderId", default=None)
    service_spec: Optional[ServiceSpec] = Field(alias="serviceSpecification", default=None)
    service_spec_characteristic: Optional[List[ServiceSpecCharacteristic]] = \
        Field(alias="serviceCharacteristic", default=[])
    supporting_service: Optional[List["ServiceInventory"]] = Field(alias="supportingService", default=[])
