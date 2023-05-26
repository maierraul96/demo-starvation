from syneto_api import APIException, Authentication, APIClientBase
from loguru import logger
from utils import *
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)



AUTH_SERVICE = "https://{0}/api/auth"
HERCULES_SERVICE = "https://{0}/api/bwmanager"

WAITING_STATES = ["WAITING"]
RUNNING_STATES = ["STARTING", "RUNNING_WITHOUT_PID", "RUNNING"]
FINISHED_STATES = ["FINISHED"]


class APIHercules(APIClientBase):
    def __init__(self, url_base=None, **kwargs):
        super().__init__(url_base, **kwargs)

    def get_process(self):
        return self.get_request("/process")

    def get_configs(self):
        return self.get_request("/configs")

    def get_total_bandwidth(self):
        return self.get_request("/configs/TOTAL_BANDWIDTH")

    def get_starvation_limit(self):
        return self.get_request("/configs/STARVATION_LIMIT")

    def patch_total_bandwidth(self, bandwidth: int):
        logger.debug(f"Update TOTAL_BANDWITH to {bandwidth}")
        return self.patch_request("configs/{key}", key="TOTAL_BANDWIDTH", body={"value": bandwidth})

    def patch_starvation_limit(self, bandwidth: int):
        logger.debug(f"Update STARVATION_LIMIT to {bandwidth}")
        return self.patch_request("configs/{key}", key="STARVATION_LIMIT", body={"value": bandwidth})

    def post_bandwidth_request(self, ref_id, priority, namespace):
        logger.debug(f"Request bandwidth for {ref_id}")
        payload = {
            "referenceId": ref_id,
            "priority": priority,
            "namespace": namespace
        }
        return self.post_request("/process", body=payload)

    def patch_bandwidth_consume(self, ref_id, pv_pid):
        logger.debug(f"Consume bandwidth for {ref_id} with pid {pv_pid}")
        return self.patch_request(f"/process/pid/{ref_id}/{pv_pid}")

    def patch_bandwidth_release(self, ref_id):
        logger.debug(f"Release bandwidth for {ref_id}")
        return self.patch_request("/process/release/{reference_id}", reference_id=ref_id)


class HerculesController:
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.hercules_api = APIHercules(url_base=HERCULES_SERVICE.format(self.host), insecure_ssl=True)
        self.process = []
        self.configs = []
        self.total_bandwidth = 0
        self.starvation_limit = 0
        self.locked_bandwidth = 0
        self.usable_bandwidth = 0
        self.login(self.user, self.password)
        self.fetch_data()

    def login(self, username: str, password: str) -> bool:
        try:
            auth_api = Authentication(url_base=AUTH_SERVICE.format(self.host), insecure_ssl=True)
            jwt = auth_api.login(username=username, password=password)["jwt"]
            self.hercules_api.set_auth_jwt(jwt)
        except Exception as e:
            logger.error(f"Login failed. {e}")
            return False
        return True

    def fetch_data(self):
        raw_process = self.hercules_api.get_process()

        self.total_bandwidth = int(self.hercules_api.get_total_bandwidth()["value"])
        self.starvation_limit = int(self.hercules_api.get_starvation_limit()["value"])

        self.process = []
        self.locked_bandwidth = 0
        for process in raw_process:
            process["bandwidth_str"] = bytes_to_mbs_str(process["bandwidth"]) if process["bandwidth"] else "--"
            process["band_per"] = get_percent_str(process["bandwidth"], self.total_bandwidth) if process["bandwidth"] else "--"
            process["pid"] = process["pid"] if process["pid"] else "--"
            self.process.append(process)

            if process["state"] == "RUNNING_WITHOUT_PID":
                self.locked_bandwidth += process["bandwidth"]
        self.usable_bandwidth = self.total_bandwidth - self.locked_bandwidth

    def get_running_process(self):
        return filter(lambda x: x["state"] in RUNNING_STATES, self.process)

    def get_waiting_process(self):
        return filter(lambda x: x["state"] in WAITING_STATES, self.process)

    def get_finished_process(self):
        return filter(lambda x: x["state"] in FINISHED_STATES, self.process)

    def collect_metrics(self):
        return f"""
    TOTAL_BANDWIDTH: {self.total_bandwidth}
    STARVATION_LIMIT: {self.starvation_limit}
    LOCKED_BANDWIDTH: {self.locked_bandwidth}
    USABLE_BANDWIDTH: {self.usable_bandwidth}
    LOCKED_PERCENT: {get_percent_str(self.locked_bandwidth, self.total_bandwidth)}
        """

    def update_total_bandwidth(self, bandwidth: int):
        self.hercules_api.patch_total_bandwidth(bandwidth)

    def update_starvation_limit(self, bandwidth: int):
        self.hercules_api.patch_starvation_limit(bandwidth)

    def request_bandwidth(self, ref_id, priority, namespace):
        self.hercules_api.post_bandwidth_request(ref_id, priority, namespace)

    def consume_bandwidth(self, ref_id, pv_pid):
        self.hercules_api.patch_bandwidth_consume(ref_id, pv_pid)

    def release_bandwidth(self, ref_id):
        self.hercules_api.patch_bandwidth_release(ref_id)

