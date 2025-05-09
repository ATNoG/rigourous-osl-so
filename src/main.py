import asyncio
import logging
import time

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

from apis.security_orchestrator import SecurityOrchestrator
from connectors.tmf_api_connector import TmfApiConnector
from models.mtd_action import MtdAction
from models.service_order import ServiceOrder
from models.service_spec import ServiceSpec, ServiceSpecWithAction
from models.so_policy import ChannelProtectionPolicy, FirewallPolicy, SiemPolicy, TelemetryPolicy
from settings import settings

VERSION = 2

description = """
NMTD performs Moving Target Defense operations on KNF-based network services.
"""

metadata_tags = [
    {
        "name": "Services",
        "description": "Service Specification updates in OpenSlice."
    },
    {
        "name": "Service Orders",
        "description": "Lists all active Service Orders in OpenSlice."
    },
    {
        "name": "Service Specifications",
        "description": "Lists all Service Specifications in OpenSlice."
    },
    {
        "name": "Security Orchestrator Policies",
        "description": "Handles policies from Security Orchestrator."
    }
]

logging_level = {
    "ERROR": logging.ERROR,
    "WARN": logging.WARN,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG
}
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging_level.get(settings.log_level.upper(), logging.DEBUG), format='%(asctime)s %(levelname)s: %(message)s')

async def handle_mtd_actions(openslice_host: str):
    mtd_actions: Dict[str, List[MtdAction]] = {}
    tmf_api_connector = TmfApiConnector(f"http://{openslice_host}")
    while True:
        start_time = time.monotonic()
        _update_mtd_actions_from_service_orders(mtd_actions, tmf_api_connector)
        _update_service_orders(mtd_actions, tmf_api_connector)
        elapsed_time = time.monotonic() - start_time
        logging.debug(f"Elapsed time: {elapsed_time}")
        await asyncio.sleep(max(60.0 - elapsed_time, 1.0))

def _update_mtd_actions_from_service_orders(mtd_actions: Dict[str, List[MtdAction]], tmf_api_connector: TmfApiConnector):
    active_service_order_ids = [service_order.id for service_order in tmf_api_connector.list_active_service_orders()]
    for service_order_id in active_service_order_ids:
        service_order = tmf_api_connector.get_service_order(service_order_id)
        if service_order:
            list_of_mtd_actions = MtdAction.from_service_order(service_order, mtd_actions.get(service_order_id, []))
            if list_of_mtd_actions:
                mtd_actions[service_order_id] = list_of_mtd_actions
    logging.debug(f"Scheduled MTD actions: {mtd_actions}")

def _update_service_orders(mtd_actions: Dict[str, List[MtdAction]], tmf_api_connector: TmfApiConnector):
    for service_order_id, value in mtd_actions.items():
        service_order_characteristics = []
        for mtd_action in value:
            service_characteristic = mtd_action.decrement_time_and_get_service_spec_characteristic_if_zero()
            if service_characteristic:
                service_order_characteristics.append(service_characteristic)
        if service_order_characteristics:
            tmf_api_connector.update_service_order_characteristics(service_order_id, ServiceSpec(serviceSpecCharacteristic=service_order_characteristics))
            logging.debug(f"Updating Service Order {service_order_id} with characteristics {service_order_characteristics}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(handle_mtd_actions(settings.openslice_host))
    yield
    task.cancel()
    asyncio.gather(task, return_exceptions=True)

app = FastAPI(
    lifespan=lifespan,
    title="Network-based Moving Target Defense",
    description=description,
    summary="Onboard and configure KNF-based network services.",
    version=f"0.0.{VERSION}",
    openapi_tags=metadata_tags
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get(f"/v{VERSION}/serviceOrders", tags=["Service Orders"], responses={
    status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Could not get Service Orders from OpenSlice"}
})
def list_service_orders() -> List[str]:
    return [service_order.id for service_order in TmfApiConnector().list_active_service_orders()]

@app.get(f"/v{VERSION}/serviceSpecs", tags=["Service Specifications"], responses={
    status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Could not get Service Specifications from OpenSlice"}
})
def list_service_specs() -> List[str]:
    return [service_spec.name for service_spec in TmfApiConnector().list_service_specs()]

@app.post(f"/v{VERSION}/so", tags=["Security Orchestrator Policies"], responses={
    status.HTTP_400_BAD_REQUEST: {"description": "Missing service 'name' or 'id' from provided Service Specification"},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Could not reach OpenSlice"}
})
async def handle_security_orchestrator_policy(service_spec: ServiceSpecWithAction) -> List[ServiceOrder]:
    if not service_spec.name and not service_spec.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing service 'name' or 'id' from provided Service Specification"
        )
    service_orders = []
    tmf_api_connector = TmfApiConnector(f"http://{settings.openslice_host}")
    service_order_ids = tmf_api_connector.get_ids_of_service_orders_using_service_spec(service_spec)
    logging.debug(f"Service Orders using Service Specification: {service_order_ids}")
    for service_order_id in service_order_ids:
        service_order = tmf_api_connector.update_service_order(service_order_id, service_spec)
        if service_order:
            service_orders.append(service_order)
    return service_orders

@app.post(f"/v{VERSION}" + "/osl/{service_order_id}", tags=["Services"], responses={
})
async def handle_openslice_service_order(service_order_id: str, mspl: Request) -> ServiceOrder:
    mspl_body = await mspl.body()
    security_orchestrator = SecurityOrchestrator(settings.so_host)
    if security_orchestrator.send_mspl(mspl_body):
        # DO WORK
        pass

@app.post(f"/v{VERSION}/telemetry", tags=["Security Orchestrator Policies"], responses={
})
async def handle_telemetry_policy(telemetry_configuration: TelemetryPolicy) -> List[ServiceOrder]:
    pass

@app.post(f"/v{VERSION}/firewall", tags=["Security Orchestrator Policies"], responses={
})
async def handle_firewall_policy(firewall_configuration: FirewallPolicy) -> List[ServiceOrder]:
    pass

@app.post(f"/v{VERSION}/siem", tags=["Security Orchestrator Policies"], responses={
})
async def handle_siem_policy(siem_configuration: SiemPolicy) -> List[ServiceOrder]:
    pass

@app.post(f"/v{VERSION}/channelProtection", tags=["Security Orchestrator Policies"], responses={
})
async def handle_channel_protection_policy(channel_protection_configuration: ChannelProtectionPolicy) -> List[ServiceOrder]:
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
