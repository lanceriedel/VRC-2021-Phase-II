import json
import time
import base64
from typing import Any, List


from loguru import logger
import paho.mqtt.client as mqtt

try:
    from pcc_library import VRC_Peripheral # type: ignore
except ImportError:
    from .pcc_library import VRC_Peripheral

class PCCModule(object):
    def __init__(self, serial_port):
        self.mqtt_host = "mqtt"
        self.mqtt_port = 18830

        # self.mqtt_user = "user"
        # self.mqtt_pass = "password"

        self.mqtt_client = mqtt.Client()
        # self.mqtt_client.username_pw_set(
        #     username=self.mqtt_user, password=self.mqtt_pass
        # )

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.pcc = VRC_Peripheral(serial_port)

        self.topic_prefix = "vrc/pcc"

        self.topic_map = {
            f"{self.topic_prefix}/set_base_color": self.set_base_color,
            f"{self.topic_prefix}/set_temp_color": self.set_temp_color,
            f"{self.topic_prefix}/set_servo_open_close": self.set_servo_open_close,
            f"{self.topic_prefix}/set_servo_min": self.set_servo_min,
            f"{self.topic_prefix}/set_servo_max": self.set_servo_max,
            f"{self.topic_prefix}/set_servo_pct": self.set_servo_pct,
            f"{self.topic_prefix}/set_pixel_cycle": self.set_pixel_cycle,
            f"{self.topic_prefix}/set_trigger_switch": self.set_trigger_switch,
            f"{self.topic_prefix}/set_switch_on": self.set_switch_on,
            f"{self.topic_prefix}/set_switch_on": self.set_switch_off,
            f"{self.topic_prefix}/set_laser_on": self.set_laser_on,
            f"{self.topic_prefix}/set_laser_off": self.set_laser_off,
            f"{self.topic_prefix}/reset": self.reset,
        }

    def run(self):
        self.mqtt_client.connect(host=self.mqtt_host, port=self.mqtt_port, keepalive=60)
        self.mqtt_client.loop_forever()

    def on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            #logger.debug(f"{msg.topic}: {str(msg.payload)}")

            if msg.topic in self.topic_map:
                payload = json.loads(msg.payload)
                self.topic_map[msg.topic](payload)
        except Exception as e:
            logger.exception(f"Error handling message on {msg.topic}")

    def on_connect(
        self, client: mqtt.Client, userdata: Any, rc: int, properties: mqtt.Properties=None
    ) -> None:
        logger.debug(f"Connected with result code {str(rc)}")
        for topic in self.topic_map.keys():
            logger.debug(f"PCCModule: Subscribed to: {topic}")
            client.subscribe(topic)

    def set_base_color(self, payload: dict) -> None:
        wrgb: List = payload["wrgb"]
        self.pcc.set_base_color(wrgb=wrgb)

    def set_temp_color(self, payload: dict) -> None:
        wrgb: List = payload["wrgb"]
        if "time" in payload:
            time: float = payload["time"]
        else:
            time: float = 0.5
        self.pcc.set_temp_color(wrgb=wrgb, time=time)

    def set_servo_open_close(self, payload: dict) -> None:
        servo: int = payload["servo"]
        action: str = payload["action"]
        self.pcc.set_servo_open_close(servo, action) #type: ignore #TODO - nathan, why is this mad?

    def set_servo_min(self, payload: dict) -> None:
        servo: int = payload["servo"]
        pulse: int = payload["min_pulse"]
        self.pcc.set_servo_min(servo, pulse)

    def set_servo_max(self, payload: dict) -> None:
        servo: int = payload["servo"]
        pulse: int = payload["max_pulse"]
        self.pcc.set_servo_max(servo, pulse)

    def set_pixel_cycle(self, payload: dict) -> None:
        target_pixel: int = payload["target_pixel"]
        delay_ms: int = payload["delay_ms"]
        self.pcc.set_pixel_cycle( target_pixel,delay_ms)

    def set_trigger_switch(self, payload: dict) -> None:
        which_switch: int = payload["which_switch"]
        how_long: int = payload["how_long"]
        self.pcc.set_trigger_switch( which_switch,how_long)

    def set_switch_on(self, payload: dict) -> None:
        which_switch: int = payload["which_switch"]
        self.pcc.set_switch_on( which_switch)

    

    def set_switch_off(self, payload: dict) -> None:
        which_switch: int = payload["which_switch"]
        self.pcc.set_switch_off( which_switch)
    def set_laser_on(self, payload) -> None:
        logger.info(f"About to laser on")
        self.pcc.set_laser_on( )

    def set_laser_off(self, payload) -> None:
        logger.info(f"About to laser off")
        self.pcc.set_laser_off( )


    def set_servo_pct(self, payload: dict) -> None:
        servo: int = payload["servo"]
        percent: int = payload["percent"]
        self.pcc.set_servo_pct(servo, percent)

    def reset(self, payload) -> None:
        self.pcc.reset_vrc_peripheral()


if __name__ == "__main__":
    pcc = PCCModule("/dev/ttyACM0")
    pcc.run()
