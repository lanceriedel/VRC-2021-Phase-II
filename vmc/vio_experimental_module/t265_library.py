from typing import Dict
import subprocess
from loguru import logger
from colored import fore, back, style

class T265(object):
    '''
    Realsense T265 Tracking Camera interface. Manages pulling data off of the camera for use by the transforms to get it in the correct reference frame.
    '''
    def __init__(self):
        self.pipe = None

    def get_rs_devices(self) -> Dict:
        """ Get Serial numbers of connected RealSense devices"""
        rs_devices = {}
        

        return rs_devices

    def setup(self) -> None:
        try:
            # Reference to a post showing how to use multiple camera: https://github.com/IntelRealSense/librealsense/issues/1735
            logger.debug("Obtaining connected RealSense devices...")
            
            # very ancedotally, running this before trying to open the connection seems to help
            subprocess.run(["rs-enumerate-devices"], check=True)

            rs_devices = self.get_rs_devices()

            logger.debug("Obtaining T265 connection ID...")
            
            logger.debug("Creating RealSense context")

            logger.debug("Creating RealSense pipeline")
            logger.debug("Creating T265 config")

            logger.debug("Enabling T265 device")
            logger.debug("Enabling T265 stream")
            logger.debug("Starting RealSense pipeline")
            logger.debug("T265 fully connected")

        except Exception as e:
            logger.exception(f"{fore.RED}T265: Error connecting to Realsense Camera: {e}{style.RESET}")
            raise e

    def get_pipe_data(self) -> str:
        # Wait for the next set of frames from the camera
        frames = self.pipe.wait_for_frames()

        # # Fetch pose frame
        pose = frames.get_pose_frame()
        
        if pose: # is not None
            data = pose.get_pose_data()
            return data
    
    def stop(self) -> None:
        try:
            logger.debug("Closing RealSense pipeline")
            self.pipe.stop()
        except:
            logger.exception("Couldn't stop the pipe")