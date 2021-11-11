# This imports the "json" module from the Python standard library
# https://docs.python.org/3/library/json.html
import json
from time import sleep
from colour import Color



# This is outside the scope of beginner Python and VRC, but this is for
# something called "type-hin    ting" that makes Python code easier to debug
from typing import Any, Callable, Dict

# This imports the Paho MQTT library that we will use to communicate to
# other running processes
# https://github.com/eclipse/paho.mqtt.python
import paho.mqtt.client as mqtt

# This creates a new class that will contain multiple functions
# which are known as "methods"
class Sandbox():
    # The "__init__" method of any class is special in Python. It's what runs when
    # you create a class like `sandbox = Sandbox()`. In here, we usually put
    # first-time initialization and setup code. The "self" argument is a magic
    # argument that must be the first argument in any class method. This allows the code
    # inside the method to access class information.
    def __init__(self) -> None:
        # Create a string attribute to hold the hostname/ip address of the MQTT server
        # we're going to connect to (an attribute is just a variable in a class).
        # Because we're running this code within a Docker Compose network,
        # using the container name of "mqtt" will work.
        self.mqtt_host = "mqtt"
        self.isdropping1=0
        # Create an integer attribute to hold the port number of the MQTT server
        # we're going to connect to. MQTT uses a default of port 1883, but we'll
        # add a zero, so as to not require administrator priviledges from the host
        # operating system by using a low port number.
        self.mqtt_port = 18830
        # Create an attribute to hold an instance of the Paho MQTT client class
        self.mqtt_client = mqtt.Client()

        # This part is a little bit more complicated. Here, we're assigning the
        # attributes of the Paho MQTT client `on_connect` and `on_message` to handles
        # of methods in our Sandbox class, which are defined below.
        # This isn't *running* those methods, but rather creating a reference to them.
        # Once we start running the Paho MQTT client, this tells the client to execute
        # these methods after it establishes the connection, and after every message
        # it recieves, respectfully.
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Create a string attribute to hold the commonly used prefix used in MQTT topics
        self.topic_prefix = "vrc"

        # Here, we're creating a dictionary of MQTT topic names to method handles
        # (as we discussed above). A dictionary is a data structure that allows use to
        # obtain values based on keys. Think of a dictionary of state names as keys
        # and their capitals as values. By using the state name as a key, you can easily
        # find the associated capital. However, this does not work in reverse. So here,
        # we're creating a dictionary of MQTT topics, and the methods we want to run
        # whenever a message arrives on that topic.
        self.topic_map: Dict[str, Callable[[dict], None]] = {
            # This is what is known as a "f-string". This allows you to easily inject
            # variables into a string without needing to combine lots of
            # strings together. Scroll down farther to see what `self.show_velocity` is.
            # https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python
            f"{self.topic_prefix}/velocity": self.show_velocity,
            f"{self.topic_prefix}/mytestopen": self.open_servo,
            f"{self.topic_prefix}/mytestclose": self.close_servo,
            "vrc/apriltags/visible_tags": self.visible_apriltag,
           

        }

    # Create a new method to effectively run everything.
    def run(self) -> None:
        # Connect the Paho MQTT client to the MQTT server with the given host and port
        # The 60 is a keep-alive timeout that defines how long in seconds
        # the connection should stay alive if connection is lost.
        self.mqtt_client.connect(host=self.mqtt_host, port=self.mqtt_port, keepalive=60)
        # This method of the Paho MQTT client tells it to start running in a loop
        # forever until it is stopped. This is a blocking function, so this line
        # will run forever until the entire program is stopped. That is why we've
        # setup the `on_message` callback you'll see below.
        self.mqtt_client.loop_forever()

    # As we described above, this method runs after the Paho MQTT client has connected
    # to the server. This is generally used to do any setup work after the connection
    # and subscribe to topics.
    def on_connect(self, client: mqtt.Client, userdata: Any, rc: int, properties: mqtt.Properties = None) -> None:
        # Print the result code to the console for debugging purposes.
        print(f"Connected with result code {str(rc)}")
        # After the MQTT client has connected to the server, this line has the client
        # connect to all topics that begin with our common prefix. The "#" character
        # acts as a wildcard. If you only wanted to subscribe to certain topics,
        # you would run this method multiple times with the exact topics you wanted
        # each time, such as:
        # client.subscribe(f"{self.topic_prefix}/velocity")
        # client.subscribe(f"{self.topic_prefix}/location")
        client.subscribe(f"{self.topic_prefix}/#")

        # If you wanted to be more clever, you could also iterate through the topic map
        # in the `__init__` method, and subscribe to each topic in the keys.
        # For example:
        # for topic in self.topic_map.keys():
        #     client.subscribe(topic)

    # As we described above, this method runs after any message on a topic
    # that has been subscribed to has been recieved.
    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        # Print the topic name and the message payload to the console
        # for debugging purposes.
        #print(f"{msg.topic}: f{str(msg.payload)}")

        # First, check if the topic of the message we've recieved is inside the topic
        # map we've created.
        if msg.topic in self.topic_map:
            print(f"{msg.topic}: f{str(msg.payload)}")
            # We can't send JSON (dictionary) data over MQTT, so we send it as an
            # encoded string. Here, we convert that encoded string back to
            # JSON information for convience.
            payload = json.loads(msg.payload)
            # Lookup the method for the topic, and execute it
            # (with the parentheses) and pass it the payload of the message.
            self.topic_map[msg.topic](payload)

        # By not creating an `else` statement here, we effectively discard
        # any message that wasn't from a topic in our topic map.

    # ================================================================================
    # Now the training wheels come off! Write your custom message handlers here.
    # Below is a very simple example to look at it. Ideally, you would want to
    # have a message handler do something more useful than just printing to
    # the console.
    def show_velocity(self, data: dict) -> None:
        vx = data["vX"]
        vy = data["vY"]
        vz = data["vZ"]
        v_ms = (vx, vy, vz)
        print(f"Velocity information: {v_ms} m/s")

        # v_fts = tuple([v * 3.28084 for v in v_ms])
        # print(f"Velocity information: {v_fts} ft/s")

    # ================================================================================
    # Here is an example on how to publish a message to an MQTT topic to
    # perform an action
    def close_servo(self,data: dict) -> None:
        # First, we construct a dictionary payload per the documentation.
        data = {"servo": 0, "action": "close"}
        # This creates it all in one line, however, you could also create it in multiple
        # lines as shown below.
        # data = {}
        # data["servo"] = 0
        # data["action"] = "open"

        # Now, we convert the dictionary to a JSON encoded string that we can publish.
        payload = json.dumps(data)

        # Finally, we publish the payload to the topic, once again using f-strings to
        # re-use our common prefix.
        self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_servo_open_close", payload=payload)

    def open_servo(self,data: dict) -> None:
        # First, we construct a dictionary payload per the documentation.
        data = {"servo": 0, "action": "open"}
        # This creates it all in one line, however, you could also create it in multiple
        # lines as shown below.
        # data = {}
        # data["servo"] = 0
        # data["action"] = "open"

        # Now, we convert the dictionary to a JSON encoded string that we can publish.
        payload = json.dumps(data)

        # Finally, we publish the payload to the topic, once again using f-strings to
        # re-use our common prefix.
        self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_servo_open_close", payload=payload)
   
    def parse_hex_color(self,color):
        rgb = color.get_rgb()
        return tuple(round(c*255) for c in rgb)

    def send_color_by_distance_mesg(self,distance):

            print(f"::::::Ready to send color DISTANCE msg: {distance} ") 
            yellow = Color("yellow")
            colors = list(yellow.range_to(Color("purple"),30))
            sendcolor = [255, 255, 255, 255]
            if distance > 29:
                distance = 29
            colorid = round(distance)

            hexcolorval = colors[colorid]
            rgbtuple = self.parse_hex_color(hexcolorval)
            sendcolor[1] = rgbtuple[0]
            sendcolor[2] = rgbtuple[1]
            sendcolor[3] = rgbtuple[2]

            msg = {
                        "wrgb": sendcolor
                        }
            debugmsg = json.dumps(msg)
            print(f":Sending color DISTANCE msg: {debugmsg} ") 
            self.mqtt_client.publish(f"vrc/pcc/set_base_color", json.dumps(msg)) 

    def send_color_mesg(self, color):

            print(f"::::::Ready to send color msg: {color} ") 

            blue = [255, 0, 0, 255]
            red = [255, 255, 0, 0]
            green = [255, 0, 255, 0]
            yellow = [255,255,255,0]
            orange = [255,255,40,0]
            purple = [255,138,0,139]


            if color=='orange':
                msg = {
                        "wrgb": orange
                        }
            elif color=='red':
                msg = {
                        "wrgb": red
                        }
            elif color=='blue':
                msg = {
                        "wrgb": blue
                        }
            elif color=='green':
                msg = {
                        "wrgb": green
                        }
            elif color=='purple':
                msg = {
                        "wrgb": purple
                        }
            else: 
                msg = {
                        "wrgb": yellow
                        }   

            debugmsg = json.dumps(msg)
            print(f":Sending color msg: {debugmsg} ") 
            self.mqtt_client.publish(f"vrc/pcc/set_base_color", json.dumps(msg))  

    def visible_apriltag(self,data: dict) -> None:
            #NOTE: this allows you to map tag id servo number -- (first slot is bogus because of 0 count e.g. tagid 1 = servo 0, tagid 2 = servo 1)  
            tagidmap=[0, 0,1,3]


            tag = data[0]
            tagid = tag["id"]

            heading = tag["heading"] 
            which_pixel = (int)(heading/360)*32
                #{"target_pixel":16,"delay_ms":250}
                #vrc/pcc/set_pixel_cycle
            datamsgpixl = {"target_pixel": which_pixel, "delay_ms": 25}
            payloadpixl = json.dumps(datamsgpixl)
            self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_pixel_cycle", payload=payloadpixl)

            #Change colors for pathways
            if (tagid==5):
                self.send_color_mesg("red") 
            elif (tagid==6):
                self.send_color_mesg("green")
            elif (tagid==7):
                self.send_color_mesg("blue") 

            #Handle building/package drops  
            else:
                horizontal_dist = tag["horizontal_dist"] 
                vertical_dist = tag["vertical_dist"] 
               

                print(f"heading: {heading} ")
                print(f"vertical_dist: {vertical_dist} ")
                print(f"****** XXhorizontal_dist: {horizontal_dist} ")
                
                
                if (horizontal_dist<10):

                    print(f"******------------- ABOUT TO DROP, TURNING GREEN!!!!!!!!!!!!!!****************")
                    self.send_color_mesg("green") 
    
                    print(f"******!!!!!!!!!!!! SERVO DROP:: tagid:{tagid} servo num: {tagidmap[tagid]}!!!!!!!!!!!!!!****************")

                    datamsg = {"servo": tagidmap[tagid], "action": "open"}
                    payload = json.dumps(datamsg)
                    self.mqtt_client.publish(topic=f"{self.topic_prefix}/pcc/set_servo_open_close", payload=payload)
                    


                elif (horizontal_dist>10):
                    print(f"******------COLOR GRADIENT!!!!!!!!!!!!!****************")
                    self.send_color_by_distance_mesg(horizontal_dist)  
                
            # elif (horizontal_dist>30):
                #    self.send_color_mesg("orange")  

                
        

if __name__ == "__main__":
    box = Sandbox()
    box.run()
