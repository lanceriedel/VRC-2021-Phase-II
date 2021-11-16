from typing import Dict
import subprocess
from loguru import logger
from colored import fore, back, style
import pyzed.sl as sl


class ZEDCamera(object):
    '''
    ZED Tracking Camera interface. Manages pulling data off of the camera for use by the transforms to get it in the correct reference frame.
    '''
    def __init__(self):
        self.pipe = None


    def setup(self) -> None:
        try:
            # Create a Camera object
            logger.debug("Starting Camera initialization -- pyzed.sl loaded")

            self.zed = sl.Camera()
            logger.debug("Created Camera obj")

            # Create a InitParameters object and set configuration parameters
            init_params = sl.InitParameters()
            init_params.camera_resolution = sl.RESOLUTION.HD720  # Use HD720 video mode (default fps: 60)
            # Use a right-handed Y-up coordinate system
            init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP
            init_params.coordinate_units = sl.UNIT.METER  # Set units in meters

            # Open the camera
            err = self.zed.open(init_params)
            logger.debug("Zed Camera Loaded/open")

            if err != sl.ERROR_CODE.SUCCESS:
                exit(1)
            logger.debug("Zed Camera Loaded/open (Success)")


            # Enable positional tracking with default parameters
            py_transform = sl.Transform()  # First create a Transform object for TrackingParameters object
            self.tracking_parameters = sl.PositionalTrackingParameters(_init_pos=py_transform)
            err = self.zed.enable_positional_tracking(self.tracking_parameters)
            if err != sl.ERROR_CODE.SUCCESS:
                exit(1)

            logger.debug("Zed Camera Enabled positional tracking")

            # Track the camera position during 1000 frames
            i = 0
            self.zed_pose = sl.Pose()
            self.zed_sensors = sl.SensorsData()
            self.zed.get_position(self.zed_pose, sl.REFERENCE_FRAME.WORLD)
            self.zed.get_sensors_data(self.zed_sensors, sl.TIME_REFERENCE.IMAGE)
            self.zed_imu = self.zed_sensors.get_imu_data()
            self.last_pos = [0,0,0]

            self.runtime_parameters = sl.RuntimeParameters()

        except Exception as e:
            logger.exception(f"{fore.RED}ZED: Error connecting to ZED Camera: {e}{style.RESET}")
            raise e

    def get_pipe_data(self) -> str:
        #logger.debug("Getting pipe data")    
            #Ok if returns none if not available -- will get called again
        if self.zed.grab(self.runtime_parameters) == sl.ERROR_CODE.SUCCESS:
            try:
                #logger.debug("Zed Camera Successfully grabbed params")
                # Get the pose of the left eye of the camera with reference to the world frame
                self.zed.get_position(self.zed_pose, sl.REFERENCE_FRAME.WORLD)
                #logger.debug("Zed Camera Successfully go position data")

                self.zed.get_sensors_data(self.zed_sensors, sl.TIME_REFERENCE.IMAGE)
                #logger.debug("Zed Camera Successfully got sensor data")

                self.zed_imu = self.zed_sensors.get_imu_data()

                #logger.debug("Zed Camera Successfuly get imu data")

                # Display the translation and timestamp
                py_translation = sl.Translation()
                tx = self.zed_pose.get_translation(py_translation).get()[0]
                ty = self.zed_pose.get_translation(py_translation).get()[1]
                tz = self.zed_pose.get_translation(py_translation).get()[2]
                #logger.debug("Translation: Tx: {0}, Ty: {1}, Tz {2}, Timestamp: {3}\n".format(tx, ty, tz, self.zed_pose.timestamp.get_milliseconds()))
                #print("Translation: Tx: {0}, Ty: {1}, Tz {2}, Timestamp: {3}\n".format(tx, ty, tz, self.zed_pose.timestamp.get_milliseconds()))

                # Display the orientation quaternion
                py_orientation = sl.Orientation()
                #ox = self.zed_pose.get_orientation(py_orientation).get()[0]
                #oy = self.zed_pose.get_orientation(py_orientation).get()[1]
                #oz = self.zed_pose.get_orientation(py_orientation).get()[2]
                #ow = self.zed_pose.get_orientation(py_orientation).get()[3]
                #rotation = self.zed_pose.get_orientation(py_orientation).get_rotation_matrix()
                #print("Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))
                #logger.debug("Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))
                
                #Display the IMU acceleratoin
    #           acceleration = [0,0,0]
    #           self.zed_imu.get_linear_acceleration(acceleration)
    #           ax = (acceleration[0], 3)
    #           ay = (acceleration[1], 3)
    #           az = (acceleration[2], 3)
    #           print("IMU Acceleration: Ax: {0}, Ay: {1}, Az {2}\n".format(ax, ay, az))
    #           logger.debug("IMU Acceleration: Ax: {0}, Ay: {1}, Az {2}\n".format(ax, ay, az))
                
                current_time = self.zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)
                diffx = abs(tx - self.last_pos[0])
                diffy = abs(ty - self.last_pos[1])
                diffz = abs(tz - self.last_pos[2])
                time_diff = current_time - self.last_time 
                a_velocity = [diffx/time_diff, diffy/time_diff, diffz/time_diff]
                self.last_time = current_time
                self.zed_imu.get_angular_velocity(a_velocity)
                #vx = (a_velocity[0], 3)
                #vy = (a_velocity[1], 3)
                #vz = (a_velocity[2], 3)
                #print("IMU Angular Velocity: Vx: {0}, Vy: {1}, Vz {2}\n".format(vx, vy, vz))
                #logger.debug("IMU Angular Velocity: Vx: {0}, Vy: {1}, Vz {2}\n".format(vx, vy, vz))

                # Display the IMU orientation quaternion
    #           self.zed_imu_pose = sl.Transform()
    #           ox = (zed_imu.get_pose(self.zed_imu_pose).get_orientation().get()[0], 3)
    #           oy = (zed_imu.get_pose(self.zed_imu_pose).get_orientation().get()[1], 3)
    #           oz = (zed_imu.get_pose(self.zed_imu_pose).get_orientation().get()[2], 3)
    #           ow = (zed_imu.get_pose(self.zed_imu_pose).get_orientation().get()[3], 3)
    #           print("IMU Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))
    #           logger.debug("IMU Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))

            #assemble return value
                #rotation =  {"w": ow, "x" : ox , "y" : oy, "z" : oz}
                rotation = self.zed_pose.get_orientation(py_orientation).get()
                translation =   {"x" : tx, "y" : ty, "z" : tz}
                velocity = a_velocity
                data = {"rotation" : rotation, "translation" : translation, "velocity" : velocity, "tracker_confidence":0x3,"mapper_confidence":0x3}

                return data

                    #  print("IMU Angular Velocity: {} [deg/sec]".format(angular_velocity))
            except OSError as err:
                logger.debug("OS error: {0}".format(err))
            except ValueError as err:
                logger.debug(f"Could not convert data:  {err}, {type(err)}")
            except BaseException as err:
                logger.debug(f"Unexpected {err}, {type(err)}")
                raise
    #quaternion = [
    #           data.rotation.w,
    #          data.rotation.x,
    #          data.rotation.y,
    #          data.rotation.z,
    #      ]
    #      position = [
    #          data.translation.x * 100,
    #          data.translation.y * 100,
    #          data.translation.z * 100,
    #      ]  # cm
    #      velocity = np.transpose(
    #          [data.velocity.x * 100, data.velocity.y * 100, data.velocity.z * 100, 0]
    #      )  # cm/s
    #      data.tracker_confidence,   -- Pose confidence 0x0 - Failed, 0x1 - Low, 0x2 - Medium, 0x3 - High
    #      data.mapper_confidence,    --Pose map confidence 0x0 - Failed, 0x1 - Low, 0x2 - Medium, 0x3 - High'


    # if ts_handler.is_new(sensors_data.get_imu_data()):
    #  quaternion = sensors_data.get_imu_data().get_pose().get_orientation().get()
    #  print("IMU Orientation: {}".format(quaternion))
    #  linear_acceleration = sensors_data.get_imu_data().get_linear_acceleration()
    #  print("IMU Acceleration: {} [m/sec^2]".format(linear_acceleration))
    #  angular_velocity = sensors_data.get_imu_data().get_angular_velocity()




### OLD
      #      frames = self.pipe.wait_for_frames()

            # # Fetch pose frame
          #  pose = frames.get_pose_frame()
        
        #data.rotation.w,
        #data.translation.x
        #data.velocity
        #
            #if pose: # is not None
             #   data = pose.get_pose_data()
              #  return data
    
    def stop(self) -> None:
        try:
            logger.debug("Closing ZED pipeline")
            self.pipe.stop()
        except:
            logger.exception("Couldn't stop the pipe")
