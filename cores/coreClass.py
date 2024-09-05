import time

class coreClass:
    def __init__(self, device=None) -> None:
        self.device = device

    def class_method(self, input_data:str) -> list[str, float]:
        start_time = time.time()
        time.sleep(1.5)

        return input_data, time.time() - start_time
