# python standard library
import os
import threading
import time
import json
import board
import adafruit_amg88xx
from colored import fore, back, style
import base64
import neopixel_spi as neopixel

from setproctitle import setproctitle

print("finished basic imports")

# pip installed packages
from loguru import logger
import paho.mqtt.client as mqtt

from typing import Any

print("finished all imports")

# find the file path to this file
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

INTERRUPTED = False

NUM_PIXELS = 12
PIXEL_ORDER = neopixel.GRB
COLORS = (0xFF0000, 0x00FF00, 0x0000FF)
DELAY = 0.1


class Thermal(object):
    def __init__(self):

        self.mqtt_host = "mqtt"
        self.mqtt_port = 18830

        self.mqtt_client = mqtt.Client()

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.topic_prefix = "vrc/thermal"

        
        self.topic_map = {
            "vrc/thermal/request_thermal_reading":self.request_thermal_reading,
            "vrc/thermal/light_status":self.light_status,
        }

        print("connecting to thermal camera...")
        i2c = board.I2C()
        self.amg = adafruit_amg88xx.AMG88XX(i2c)
        print("Connected to Thermal Camera!")


        self.spi = board.SPI()

        self.pixels = neopixel.NeoPixel_SPI(self.spi,
                                    NUM_PIXELS,
                                    pixel_order=PIXEL_ORDER,
                                    auto_write=False)


    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            #logger.debug(f"{msg.topic}: {str(msg.payload)}")
            if msg.topic in self.topic_map:
                payload = json.loads(msg.payload)
                self.topic_map[msg.topic](payload)
        except Exception as e:
            logger.debug(f"{fore.RED}Error handling message on {msg.topic}{style.RESET}") #type: ignore
            print(e)

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
        properties: mqtt.Properties = None,
    ) -> None:
        logger.debug(f" THERAM: Connected with result code {str(rc)}")
        for topic in self.topic_map.keys():
            logger.debug(f"THERMAL: Subscribed to: {topic}")
            client.subscribe(topic)

    def request_thermal_reading(self, msg: dict):
        reading = bytearray(64)
        i=0
        for row in self.amg.pixels:
            for pix in row:
                pixasint = round(pix)
                bpix=pixasint.to_bytes(1, 'big')
                reading[i]=bpix[0]
                i+=1
        base64Encoded = base64.b64encode(reading)
        #logger.debug(str(base64Encoded))
        base64_string = base64Encoded.decode('utf-8')

        thermalreading = { "reading":  base64_string}
        self.mqtt_client.publish(
                f"{self.topic_prefix}/thermal_reading",
                json.dumps(thermalreading),
                retain=False,
                qos=0,
            )


    def light_status(self, msg: dict):
        for color in COLORS:
            for i in range(NUM_PIXELS):
                self.pixels[i] = color
                self.pixels.show()
                time.sleep(DELAY)
                self.pixels.fill(0)

    def request_thread(self):
        msg={}
        while True:
            self.request_thermal_reading(msg)
            time.sleep(.2)
        

    def run(self):
        # tells the os what to name this process, for debugging
        setproctitle("thermal_process")
        # allows for graceful shutdown of any child threads

        self.mqtt_client.connect(host=self.mqtt_host, port=self.mqtt_port, keepalive=60)
        
        request_thread = threading.Thread(
            target=self.request_thread, args=(), daemon=True, name="request_thread"
        )
        request_thread.start()

        self.mqtt_client.loop_forever()

if __name__ == "__main__":
    thermal = Thermal()
    thermal.run()
