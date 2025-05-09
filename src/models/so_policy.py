from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class PolicyType(str, Enum):
    CHANNEL_PROTECTION = "channel_protection"
    FIREWALL = "firewall"
    TELEMETRY = "telemetry"
    SIEM = "siem"

class ChannelProtectionPolicy(BaseModel):
    local_address: Optional[str] = None
    remote_address: Optional[str] = None
    encryption_key_1: Optional[str] = Field(alias="enc_key_1", default=None)
    encryption_key_2: Optional[str] = Field(alias="enc_key_2", default=None)
    integrity_key_1: Optional[str] = Field(alias="int_key_1", default=None)
    integrity_key_2: Optional[str] = Field(alias="int_key_2", default=None)
    
class FirewallPolicy(BaseModel):
    name: Optional[str] = None
    source_address: Optional[str] = Field(alias="srcAddr", default=None)
    destination_address: Optional[str] = Field(alias="dstAddr", default=None)
    action: Optional[str] = None

class SiemPolicy(BaseModel):
    pass

class TelemetryConfiguration(BaseModel):
    domain_id: Optional[str] = Field(alias="domainID", default=None)
    flavor_id: Optional[str] = Field(alias="flavorID", default=None)
    exporter_endpoint: Optional[str] = Field(alias="exporterEndpoint", default=None)

class TelemetryPolicy(BaseModel):
    deploy: Optional[str] = None
    configuration: Optional[TelemetryConfiguration] = None
