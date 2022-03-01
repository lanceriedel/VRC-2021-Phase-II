# python standard library
import os
import threading
import time
import json
import board
from colored import fore, back, style
import base64
import neopixel_spi as neopixel

from setproctitle import setproctitle

print("finished basic imports")

# pip installed packages
from loguru import logger
import paho.mqtt.client as mqtt
import subprocess
from typing import Any

print("finished all imports")

# find the file path to this file
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

INTERRUPTED = False

NUM_PIXELS = 12
PIXEL_ORDER = neopixel.GRB
#RGB
COLORS = (0xFF0000, 0x00FF00, 0x0000FF)
CLR_PURPLE=0x6a0dad
CLR_AQUA=0x00FFFF
CLR_ORANGE=0xF5A506
CLR_YELLOW=0xC1E300
CLR_BLUE=0x001EE3

VIO_LED=1
PCC_LED=2
THERMAL_LED=3
FCC_LED=4
APRIL_LED=5

DELAY = 0.1


class Status(object):
    def __init__(self):
        self.initialized = False
        self.mqtt_host = "mqtt"
        self.mqtt_port = 18830

        self.mqtt_client = mqtt.Client()

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.topic_prefix = "vrc/status"

        
        self.topic_map = {
            "vrc/status/light_status":self.light_status,
            "vrc/status/light_status_PCC":self.light_status,
            "vrc/status/light_status_VIO":self.light_status,
            "vrc/status/light_status_APRIL":self.light_status,
            "vrc/status/light_status_FCC":self.light_status,
            "vrc/status/light_status_THERMAL":self.light_status
        }


        self.spi = board.SPI()

        self.pixels = neopixel.NeoPixel_SPI(self.spi,
                                    NUM_PIXELS,
                                    pixel_order=PIXEL_ORDER,
                                    auto_write=False)

        self.red_status_all()

        
    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            #logger.debug(f"{msg.topic}: {str(msg.payload)}")
            self.check_status(msg.topic)

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
        logger.debug(f"SYSTEM STATUS MODULE : Connected with result code {str(rc)}")
        for topic in self.topic_map.keys():
            logger.debug(f"STATUS: Subscribed to: {topic}")
            client.subscribe(topic)


    def set_cpu_status(self):

        ## Initialize power mode status

        batcmd="/app/nvpmodel --verbose -f /app/nvpmodel.conf -m 0"
        try:
            result = subprocess.check_output(batcmd, shell=True,stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logger.exception("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    def check_status(self, topic) :
        if 'vrc/vio' in topic: 
            self.light_up(VIO_LED,CLR_PURPLE)
        if 'vrc/pcc' in topic:
            self.light_up(PCC_LED, CLR_AQUA)
        if 'vrc/fcc' in topic:
            self.light_up(FCC_LED,CLR_ORANGE)
        if 'vrc/thermal' in topic:
            self.light_up(THERMAL_LED,CLR_BLUE)
        if 'vrc/april' in topic:
            self.light_up(APRIL_LED,CLR_YELLOW)

    def red_status_all(self):
        for i in range(NUM_PIXELS):
            self.pixels[i] = COLORS[0]
        self.pixels.show()
           


    def light_up(self, which_one, color):
        self.pixels[which_one] = color
        self.pixels.show()

    def light_status(self, msg: dict):
        for color in COLORS:
            for i in range(NUM_PIXELS):
                self.pixels[i] = color
                self.pixels.show()
                time.sleep(DELAY)
                self.pixels.fill(0)

    def status_check(self):
        if not self.initialized:
            self.initialized = True
            self.set_cpu_status()

        batcmd="/app/nvpmodel -f /app/nvpmodel.conf -q"
        try:
            result = subprocess.check_output(batcmd, shell=True,stderr=subprocess.STDOUT)
            if b'MAXN' in result:
                self.pixels[0] = COLORS[1]
            else:
                self.pixels[0] = COLORS[0]
            self.pixels.show()
        except subprocess.CalledProcessError as e:
            logger.exception("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    def status_thread(self):
        msg={}
        while True:
            self.status_check()
            time.sleep(1)
        

    def run(self):
        # tells the os what to name this process, for debugging
        setproctitle("status_process")
        # allows for graceful shutdown of any child threads

        self.mqtt_client.connect(host=self.mqtt_host, port=self.mqtt_port, keepalive=60)
        
        status_thread = threading.Thread(
            target=self.status_thread, args=(), daemon=True, name="request_status_check"
        )
        status_thread.start()

        self.mqtt_client.loop_forever()

if __name__ == "__main__":
    status = Status()
    status.run()