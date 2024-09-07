class FlowHandler:
    def __init__(self, volume_ml: int, pls: float):
        self.run_flow_cmd = f'/opt/kiosk/vodobox-pro/vendor/flowmeter/flow {volume_ml} {pls}'

    def start_pouring(self):
        pass

    def stop_pouring(self):
        pass
