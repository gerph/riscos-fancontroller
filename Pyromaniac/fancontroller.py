"""
FanController module.
"""

from riscos.errors import RISCOSSyntheticError

from riscos.modules.pymodules import PyModule
from riscos.readargs import read_args

from .constants import FanConstants


class FanDescriptor(object):
    """
    Describes a fan.
    """
    device_names = {
            FanConstants.FanType_Device_CPU: 'CPU',
            FanConstants.FanType_Device_GPU: 'GPU',
            FanConstants.FanType_Device_Memory: 'Memory',
            FanConstants.FanType_Device_IOCard: 'I/O card',
            FanConstants.FanType_Device_PSU: 'PSU',
            FanConstants.FanType_Device_Backplane: 'Backplane',
            FanConstants.FanType_Device_Chassis: 'Chassis',
            FanConstants.FanType_Device_External: 'External',
            FanConstants.FanType_Device_Generic: 'Generic',
        }
    memory_location = {
            FanConstants.FanType_Location_Memory_OnModule: "Module",
            FanConstants.FanType_Location_Memory_OnCPUBank: "CPU",
            FanConstants.FanType_Location_Memory_OnChannel: "Channel",
            FanConstants.FanType_Location_Memory_OnRiser: "Riser",
        }
    space_lateral = {
            FanConstants.FanType_Location_Space_LateralUnspecified: 'Unspecified',
            FanConstants.FanType_Location_Space_LateralLeft: 'Left',
            FanConstants.FanType_Location_Space_LateralMiddle: 'Middle',
            FanConstants.FanType_Location_Space_LateralRight: 'Right',
        }
    space_longitudinal = {
            FanConstants.FanType_Location_Space_LongitudinalUnspecified: 'Unspecified',
            FanConstants.FanType_Location_Space_LongitudinalFront: 'Front',
            FanConstants.FanType_Location_Space_LongitudinalMiddle: 'Middle',
            FanConstants.FanType_Location_Space_LongitudinalRear: 'Rear',
        }
    space_vertical = {
            FanConstants.FanType_Location_Space_VerticalUnspecified: 'Unspecified',
            FanConstants.FanType_Location_Space_VerticalLower: 'Lower',
            FanConstants.FanType_Location_Space_VerticalMiddle: 'Middle',
            FanConstants.FanType_Location_Space_VerticalUpper: 'Upper',
        }
    external_location = {
            FanConstants.FanType_Location_External_UPS: "UPS",
            FanConstants.FanType_Location_External_ExternalDrive: "Drive",
            FanConstants.FanType_Location_External_ExternalDevice: "Device",
            FanConstants.FanType_Location_External_DeskFan: "Desktop Fan",
            FanConstants.FanType_Location_External_Aircon: "Aircon",
            FanConstants.FanType_Location_External_PizzaOven: "Pizza Oven",
            FanConstants.FanType_Location_External_Unspecified: "Unspecified",
        }

    control_modes = {
            FanConstants.FanControl_Manual: "Manual",
            FanConstants.FanControl_Managed: "Managed",
            FanConstants.FanControl_AutomaticNoise: "Auto (Noise)",
            FanConstants.FanControl_AutomaticPerformance: "Auto (Perf.)",
        }

    def __init__(self, ro, location_id, provider, accuracy, maximum, speeds, capabilities, driver, driver_ws):
        self.ro = ro
        # Fan_id is assigned on registration
        self.fan_id = None
        self.location_id = location_id
        self.provider = provider
        self._provider_mem = None
        self.accuracy = accuracy
        self.maximum = maximum
        self.speeds = speeds
        self._speeds_mem = None
        self.control_mode = FanConstants.FanControl_Invalid
        self.capabilities = capabilities
        self.driver = driver
        self.driver_ws = driver_ws

    def __repr__(self):
        return "<{}(location=&{:08x}, provided by {})>".format(self.__class__.__name__,
                                                               self.location_id,
                                                               self.provider)

    def destroy(self):
        if self._provider_mem:
            self._provider_mem.free()
        if self._speeds_mem:
            self._speeds_mem.free()

    @property
    def provider_mem(self):
        if not self._provider_mem:
            self._provider_mem = self.ro.kernel.da_rma.strdup(self.provider)
        return self._provider_mem.address

    @property
    def speeds_mem(self):
        if not self.speeds:
            return 0

        if not self._speeds_mem:
            self._speeds_mem = self.ro.kernel.da_rma.allocate((len(self.speeds) + 1) * 4)
            self._speeds_mem.write_words(self.speeds)
            self._speeds_mem[len(self.speeds) + 4].word = -1
        return self._speeds_mem.address

    def location_name(self):
        device = (self.location_id >> FanConstants.FanType_Device_Shift) & FanConstants.FanType_Device_Mask
        sequence = (self.location_id >> FanConstants.FanType_Sequence_Shift) & FanConstants.FanType_Sequence_Mask
        location = (self.location_id >> FanConstants.FanType_Location_Shift) & FanConstants.FanType_Location_Mask
        device_name = self.device_names.get(device, "Device#{}".format(device))

        if device >= 16 and device <= 31:
            # Devices that report their position in space
            space = []
            lateral = (location >> FanConstants.FanType_Location_Space_LateralShift) & FanConstants.FanType_Location_Space_LateralMask
            if lateral != 0:
                space.append(self.space_lateral[lateral])

            longitudinal = (location >> FanConstants.FanType_Location_Space_LongitudinalShift) & FanConstants.FanType_Location_Space_LongitudinalMask
            if longitudinal != 0:
                space.append(self.space_longitudinal[longitudinal])

            vertical = (location >> FanConstants.FanType_Location_Space_VerticalShift) & FanConstants.FanType_Location_Space_VerticalMask
            if vertical != 0:
                space.append(self.space_vertical[vertical])

            sequence_name = ''
            if sequence:
                sequence_name = ' #{}'.format(sequence)
            return "{} {}{}".format(device_name, ', '.join(space), sequence_name)

        elif device in (FanConstants.FanType_Device_CPU,
                        FanConstants.FanType_Device_GPU,
                        FanConstants.FanType_Device_IOCard):

            sequence_name = ''
            if sequence:
                sequence_name = ' #{}'.format(sequence)
            return "{}{}".format(device_name, sequence_name)

        elif device == FanConstants.FanType_Device_Memory:
            location_name = self.memory_location.get(location, 'Loc#{}'.format(location))

            sequence_name = ''
            if sequence:
                sequence_name = ' #{}'.format(sequence)
            return "{} {}{}".format(device_name, location_name, sequence_name)

        elif device == FanConstants.FanType_Device_External:
            location_name = self.external_location.get(location, 'Loc#{}'.format(location))

            sequence_name = ''
            if sequence:
                sequence_name = ' #{}'.format(sequence)
            return "{} {}{}".format(device_name, location_name, sequence_name)

        else:
            return "&{:08x}".format(self.location_id)

    def driver_call(self, reason, rin=None, rout=None):
        if not rin:
            rin = {}
        if not rout:
            rout = []
        rin[0] = reason
        rin[1] = self.fan_id
        rin[2] = self.location_id
        rin[12] = self.driver_ws
        regs = self.ro.execute_with_error(self.driver, preserve=True, rin=rin, rout=rout)
        return regs

    def get_speed(self):
        regs = self.driver_call(FanConstants.FanDriver_GetSpeed,
                                rout=[3])
        return regs[3]

    def set_speed(self, speed):
        if not self.capabilities & FanConstants.FanCapability_SupportsManual:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_CannotSetSpeed,
                                       "Fan speed cannot be set for fan {}".format(self.fan_id))

        if self.maximum != 0 and \
           speed > self.maximum:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_CannotSetSpeed,
                                       "Fan speed cannot be set higher than {}".format(self.maximum))

        if self.accuracy and \
           speed % self.accuracy != 0:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_CannotSetSpeed,
                                       "Fan speed {} is not a multiple of {}".format(speed, self.accuracy))

        if self.speeds:
            # Check that we are one of the supported speeds
            if speed not in self.speeds:
                raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_CannotSetSpeed,
                                           "Fan speed must be set to a supported speed")

        regs = self.driver_call(FanConstants.FanDriver_SetSpeed,
                                rin={3: speed},
                                rout=[3])
        return regs[3]

    def get_control(self):
        if not (self.capabilities & (FanConstants.FanCapability_SupportsAutomatic)):
            # If it does not support automatic control, then it's manual only
            return FanConstants.FanControl_Manual

        if self.control_mode != FanConstants.FanControl_Invalid:
            # We know what the mode is; return it.
            return self.control_mode

        regs = self.driver_call(FanConstants.FanDriver_GetControlMode,
                                rout=[3])
        self.control_mode = regs[3]
        return self.control_mode

    def set_control(self, control):
        if control in (FanConstants.FanControl_Manual, FanConstants.FanControl_Managed):
            if not (self.capabilities & (FanConstants.FanCapability_SupportsManual)):
                raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_BadControlMode,
                                           "Fan cannot be configured for manual/managed control")

        elif control in (FanConstants.FanControl_AutomaticNoise,
                         FanConstants.FanControl_AutomaticPerformance):
            if not (self.capabilities & (FanConstants.FanCapability_SupportsAutomatic)):
                raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_BadControlMode,
                                           "Fan cannot be configured for automatic control")

        if self.control_mode == control:
            # It's already in this mode. No need to tell them something they already know.
            return self.control_mode

        # If they asked for managed mode, we ask the driver for manual mode, because to it
        # they're being driven manually and don't care who drives them.
        request = FanConstants.FanControl_Manual if control == FanConstants.FanControl_Managed else control
        regs = self.driver_call(FanConstants.FanDriver_SetControlMode,
                                rin={3: request},
                                rout=[3])

        self.control_mode = regs[3]
        if control == FanConstants.FanControl_Managed and regs[3] == FanConstants.FanControl_Manual:
            # Make it appear to the outside world like it's managed if that's what we requested.
            self.control_mode = FanConstants.FanControl_Managed

        return self.control_mode

    def set_location(self, new_location_id):
        if not self.capabilities & FanConstants.FanCapability_SupportsMove:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_CannotSetLocation,
                                       "Fan location cannot be changed")
        regs = self.driver_call(FanConstants.FanDriver_SetLocation,
                                rin={3: new_location_id},
                                rout=[3])
        state = regs[3]
        if state != FanConstants.FanSetLocation_OK:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_CannotSetLocation,
                                       "Fan location is not valid")

        # If it was changed ok, then we just set the new location
        self.location_id = new_location_id


class TaskPollWord(object):

    def __init__(self, ro, address, bit_dying, bit_registrations, bit_errors):
        self.ro = ro
        self.address = address
        self.memory = self.ro.memory[address]
        self.bit_dying = bit_dying
        self.bit_registrations = bit_registrations
        self.bit_errors = bit_errors

    def __repr__(self):
        return "<{}(pollword=&{:08x}, dying={}, registrations={}, errors={})>".format(self.__class__.__name__,
                                                                                      self.address,
                                                                                      self.bit_dying,
                                                                                      self.bit_registrations,
                                                                                      self.bit_errors)

    def notify_dying(self):
        if self.bit_dying != -1:
            self.memory.word |= (1<<self.bit_dying)

    def notify_registrations(self):
        if self.bit_registrations != -1:
            self.memory.word |= (1<<self.bit_registrations)

    def notify_errors(self):
        if self.bit_errors != -1:
            self.memory.word |= (1<<self.bit_errors)


class Fans(object):
    """
    Management for the registered fans.
    """

    def __init__(self, ro):
        self.ro = ro
        self.next_fan_id = 1
        # Our fans, keyed by their fan_id
        self.fans = {}
        # Pollwords, keyed by their address
        self.pollwords = {}

    def __repr__(self):
        return "<{}({} fans, {} pollwords)>".format(self.__class__.__name__,
                                                    len(self.fans),
                                                    len(self.pollwords))

    def notify_shutdown(self):
        for pw in self.pollwords.values():
            pw.notify_dying()

    def notify_registrations(self):
        for pw in self.pollwords.values():
            pw.notify_registrations()

    def notify_errors(self):
        for pw in self.pollwords.values():
            pw.notify_errors()

    def shutdown(self):
        # Deregister all fans / release memory
        for fan in self.fans.values():
            fan.destroy()
        self.fans = {}
        self.notify_shutdown()
        self.pollwords = {}

    def new_fanid(self):
        fan_id = self.next_fan_id
        self.next_fan_id += 1
        return fan_id

    def register(self, descriptor):
        fan_id = self.new_fanid()
        descriptor.fan_id = fan_id
        self.fans[fan_id] = descriptor
        # Issue service to say the fan has arrived
        self.ro.kernel.api.os_servicecall(FanConstants.Service_FanControllerFanChanged,
                                          regs={0: fan_id,
                                                2: FanConstants.Service_FanControllerFanChanged_Added})
        self.notify_registrations()
        return fan_id

    def deregister(self, fan_id):
        fan = self.find_fan(fan_id)
        del self.fans[fan_id]
        # Issue service to say the fan has been removed
        self.ro.kernel.api.os_servicecall(FanConstants.Service_FanControllerFanChanged,
                                          regs={0: fan_id,
                                                2: FanConstants.Service_FanControllerFanChanged_Removed})
        self.notify_registrations()

    def find_fan(self, fan_id):
        fan = self.fans.get(fan_id, None)
        if not fan:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_BadFan,
                                       "Bad fan identifier &{:x} specified to FanController".format(fan_id))
        return fan

    def add_pollword(self, address, bit_dying, bit_registrations, bit_errors):
        pw = TaskPollWord(self.ro, address, bit_dying, bit_registrations, bit_errors)
        self.pollwords[address] = pw

    def remove_pollword(self, address, bit_dying, bit_registrations, bit_errors):
        # Don't error if they removed something that didn't exist
        if address in self.pollwords:
            del self.pollwords[address]

    def __iter__(self):
        for fan_id, fan in sorted(self.fans.items()):
            yield fan

    def __len__(self):
        return len(self.fans)

    def __getitem__(self, index):
        return self.find_fan(index)


class FanController(PyModule):
    version = '0.02'
    date = '01 May 2020'
    swi_base = 0x10080  # FIXME: Not registered
    swi_prefix = "FanController"
    swi_names = [
            "Version",
            "Enumerate",
            "Info",
            "Speed",
            "Configure",
            "TaskPollWord",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "Register",
            "Deregister",
        ]

    entrypoint_names = [
            'init_callback_handler',
        ]

    commands = [
            ('Fans',
             "Displays information about the fans known to the system.",
             0x00000000,
             'Syntax: *Fans'),

            ('FanSpeed',
             "Displays or sets the speed of a fan.",
             0x00020001,
             'Syntax: *FanSpeed <Fan> (<Speed>)')
        ]

    api_version = 101

    def __init__(self, ro, module):
        super(FanController, self).__init__(ro, module)
        self.swi_dispatch = {
                0: self.swi_version,
                1: self.swi_enumerate,
                2: self.swi_info,
                3: self.swi_speed,
                4: self.swi_configure,
                5: self.swi_taskpollword,

                16: self.swi_register,
                17: self.swi_deregister,
            }

        self.fans = Fans(ro)

        self.debug_fancontroller = False
        self.ro.debug_register_ivar('fancontroller', self)

    def initialise(self, arguments, pwp):
        super(FanController, self).initialise(arguments, pwp)
        # Must announce our existance on a callback, as SWIs not available during initialise
        self.pwp = pwp
        self.ro.kernel.api.os_addcallback(self.module.entrypoints['init_callback_handler'].address,
                                          self.pwp)

    def init_callback_handler(self, regs):
        self.announce_initialise(FanConstants.Service_FanControllerStarted)

    def finalise(self, pwp):
        # Remove any announcement
        self.ro.kernel.api.os_removecallback(self.module.entrypoints['init_callback_handler'].address,
                                             self.pwp)

        # Issue the finalise first so that clients can know to stop calling us.
        self.announce_initialise(FanConstants.Service_FanControllerDying)
        self.fans.shutdown()

    def announce_initialise(self, state):
        """
        Announce the initialisation/finalisation state.

        @param state: The initialise/finalise state of the module
        """

        if self.debug_fancontroller:
            print("FanController: Announcing initialised/finalised: state=&{:x}".format(state))

        self.ro.kernel.api.os_servicecall(state)

    def service(self, service, regs):
        if service == FanConstants.Service_FanControllerFanChangedState:
            # A driver has notified us of an error state, so we need to update the pollwords
            self.fans.notify_errors()

    def swi(self, offset, regs):
        func = self.swi_dispatch.get(offset, None)
        if func:
            return func(regs)

        return False

    def swi_version(self, regs):
        """
        SWI FanController_Version - Read version of the API

        <=  R0 = version number of the API * 100 (1.00 for this version)
        """
        regs[0] = self.api_version

    def _return_faninfo(self, regs, fan):
        """
        Common return of fan details for a given fan.

        @param fan: fan to return details for
        """
        regs[0] = fan.fan_id
        regs[1] = fan.location_id
        regs[2] = fan.capabilities
        regs[3] = fan.provider_mem
        regs[4] = fan.accuracy
        regs[5] = fan.maximum
        regs[6] = fan.speeds_mem

    def swi_enumerate(self, regs):
        """
        SWI FanController_Enumerate - enumerate the known fans

        =>  R0 = 0 for first call, or value from previous call

        <=  R0 = fan id, or -1 if no more entries
            R1 = location id
            R2 = fan capabilty flags
            R3 = pointer to provider name
            R4 = fan speed accuracy
            R5 = maximum speed
            R6 = pointer to list of supported speeds, or 0 if arbitrary speeds (for the accuracy) may be given
        """
        search_for = regs[0]
        for fan in self.fans:
            if search_for == 0:
                # We want to return this fan.
                self._return_faninfo(regs, fan)
                return True

            elif search_for == fan.fan_id:
                # We found the fan that they want the result after, so mark as returning the next one
                search_for = 0

        # No fan found. So we're at the end of the list.
        regs[0] = -1
        return True

    def swi_info(self, regs):
        """
        SWI FanController_Info - Information about a specific fan

        =>  R0 = fan id

        <=  R0 = fan id
            R1 = location id
            R2 = fan capabilty flags
            R3 = pointer to provider name
            R4 = fan speed accuracy
            R5 = maximum speed
            R6 = pointer to list of supported speeds, or 0 if arbitrary speeds (for the accuracy) may be given
        """
        fan_id = regs[0]
        fan = self.fans.find_fan(fan_id)
        self._return_faninfo(regs, fan)
        return True

    def swi_speed(self, regs):
        """
        SWI FanController_Speed - Read or set speed of fan

        =>  R0 = fan id to read or change
            R1 = speed, or -1 to read current speed
        <=  R1 = speed of fan
        """
        fan_id = regs[0]
        new_speed = regs.signed[1]
        fan = self.fans.find_fan(fan_id)

        if new_speed == -1:
            speed = fan.get_speed()
        else:
            speed = fan.set_speed(new_speed)

        regs[1] = speed
        return True

    def swi_configure(self, regs):
        """
        SWI FanController_Configure - Configure the operation of the fan

        =>  R0 = fan id to read or change
            R1 = configure operation:
                    0: control of the fan
                    1: location of the fan
            R2 = parameter to configure
        <=  R2 = result
        """
        fan_id = regs[0]
        config = regs[1]
        fan = self.fans.find_fan(fan_id)

        result = 0

        if config == FanConstants.FanController_Configure_Control:
            param = regs.signed[2]
            if param == -1:
                result = fan.get_control()
            else:
                result = fan.set_control(param)

        elif config == FanConstants.FanController_Configure_Location:
            param = regs[2]
            fan.set_location(param)
            result = param

        else:
            raise RISCOSSyntheticError(self.ro, FanConstants.ErrorNumber_BadConfigure,
                                       "FanController_Configure operation {} not supported".format(config))

        regs[2] = result
        return True

    def swi_taskpollword(self, regs):
        """
        SWI FanController_TaskPollWord - Register or deregister a pollword

        =>  R0 = pointer to word-aligned pollword
            R1 = bit number to set for FanController_Dying, or -1 for no bit
            R2 = bit number to set for registrations, or -1 for no bit
            R3 = bit number to set for error states, or -1 for no bit
        <=  none
        """
        pollword = regs[0]
        bit_dying = regs[1]
        bit_registrations = regs[2]
        bit_errors = regs[3]

        if bit_dying == -1 and bit_registrations == -1 and bit_errors == -1:
            self.fans.remove_pollword(pollword)
        else:
            self.fans.add_pollword(pollword, bit_dying, bit_registrations, bit_errors)
        return True

    def swi_register(self, regs):
        """
        SWI FanController_Register - Register a fan driver

        =>  R0 = pointer to driver code for fan
            R1 = pointer to driver workspace for fan
            R2 = location id for new fan
            R3 = fan capabilities
            R4 = pointer to provider name
            R5 = fan accuracy
            R6 = maximum speed
            R7 = pointer to table of speeds that the fan may run at, or 0 for just fan accuracy
        <=  R0 = fan_id allocated
        """
        driver = regs[0]
        driver_ws = regs[1]
        location_id = regs[2]
        capabilities = regs[3]
        provider = self.ro.memory[regs[4]].string
        accuracy = regs[5]
        maximum = regs[6]
        speeds_ptr = regs[7]

        if speeds_ptr:
            speeds_mem = self.ro.memory[speeds_ptr]
            speeds = []
            while speeds_mem.word != -1:
                speeds.append(speeds_mem.word)
                speeds_mem.address += 4
        else:
            speeds = None

        fan = FanDescriptor(self.ro, location_id, provider, accuracy, maximum, speeds, capabilities, driver, driver_ws)
        self.fans.register(fan)
        if self.debug_fancontroller:
            print("Registered fan {!r} with id {}".format(fan, fan.fan_id))

        regs[0] = fan.fan_id

        return True

    def swi_deregister(self, regs):
        """
        SWI FanController_Deregister - Deregister a fan driver

        =>  R0 = fan id to deregister
        """
        fan_id = regs[0]
        self.fans.deregister(fan_id)

        return True

    def _speed_string(self, speed):
        if speed == FanConstants.FanState_Failed:
            speed_str = "Failed"
        elif speed == FanConstants.FanState_Disconnected:
            speed_str = "Disconnected"
        elif speed < 0:
            speed_str = "Error code {}".format(speed)
        elif speed <= 100:
            speed_str = "{}%".format(speed)
        elif speed == 101:
            speed_str = "Automatic"
        elif speed >= 200:
            speed_str = "{} RPM".format(speed)
        else:
            speed_str = "Code {}".format(speed)
        return speed_str

    def cmd_fans(self, args):
        """
        Syntax: *Fans
        """
        for fan in self.fans:
            speed = fan.get_speed()
            speed_str = self._speed_string(speed)

            control = fan.get_control()
            control_str = fan.control_modes.get(control, "Control {}".format(control))

            location_str = fan.location_name()

            self.ro.kernel.writeln("{:5} : {:<24}  {:<32}  {:9}  {}".format(fan.fan_id, fan.provider,
                                                                            location_str, control_str,
                                                                            speed_str))

    def cmd_fanspeed(self, args):
        """
        Syntax: *FanSpeed <Fan> (<Speed>)
        """
        args = read_args(self.ro, "/A,", args)

        fan_id = int(args[0].value)
        fan = self.fans.find_fan(fan_id)
        if args[1]:
            speed = int(args[1].value)
            fan.set_speed(speed)
        else:
            speed = fan.get_speed()
            speed_str = self._speed_string(speed)
            self.ro.kernel.writeln("{} : {}".format(fan_id, speed_str))
