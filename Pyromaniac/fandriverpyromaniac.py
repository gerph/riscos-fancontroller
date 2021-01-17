"""
A very rudimentary fan driver.
"""

from riscos.errors import RISCOSSyntheticError, RISCOSError

from riscos.modules.pymodules import PyModule

from .constants import FanConstants


class Fan(object):

    def __init__(self, location_id, capabilities, accuracy, maximum, speeds):
        self.fan_in = None
        if speeds:
            self.speed = max(speeds)
        else:
            self.speed = 100
        self.mode = FanConstants.FanControl_Manual
        self.speeds = speeds
        self.accuracy = accuracy
        self.maximum = maximum
        self.location_id = location_id
        self.capabilities = capabilities

    def __repr__(self):
        return "<{}(id={}, speed={}, mode={})>".format(self.__class__.__name__,
                                                       self.fan_id, self. speed, self.mode)


class FanDriverPyromaniac(PyModule):
    version = '0.01'
    date = '14 Jan 2021'

    entrypoint_names = [
            'driver',
        ]

    def __init__(self, ro, module):
        super(FanDriverPyromaniac, self).__init__(ro, module)
        self.registered = False
        self.pwp = None
        self.provider_name = None

        # The fans that we'll declare
        self.fans = [
                Fan(location_id=(((FanConstants.FanType_Location_Space_LateralLeft<<FanConstants.FanType_Location_Space_LateralShift) |
                                  (FanConstants.FanType_Location_Space_LongitudinalRear<<FanConstants.FanType_Location_Space_LongitudinalShift) |
                                  (FanConstants.FanType_Location_Space_VerticalUnspecified<<FanConstants.FanType_Location_Space_VerticalShift)) << FanConstants.FanType_Location_Shift) |
                                (0<<FanConstants.FanType_Sequence_Shift) |
                                (FanConstants.FanType_Device_Chassis<<FanConstants.FanType_Device_Shift),
                    speeds=None,
                    accuracy=10,
                    maximum=0,
                    capabilities=FanConstants.FanCapability_SupportsManual)
            ]

        self.debug_fandriverpyromaniac = False
        self.ro.debug_register_ivar('fandriverpyromaniac', self)

    def register(self):
        if self.registered:
            return

        try:
            for fan in self.fans:
                try:
                    if fan.speeds:
                        speeds_ptr = self.ro.kernel.da_rma.allocate(4 * (len(fan.speeds) + 1))
                        speeds_ptr.write_words(fan.speeds)
                        speeds_ptr[4 * len(fan.speeds)].word = -1
                    else:
                        speeds_ptr = 0

                    rout = self.ro.kernel.api.swi(FanConstants.SWIFanController_Register,
                                                  regs={0: self.module.entrypoints['driver'].address,
                                                        1: self.pwp,
                                                        2: fan.location_id,
                                                        3: fan.capabilities,
                                                        4: self.provider_name,
                                                        5: fan.accuracy,
                                                        6: fan.maximum,
                                                        7: speeds_ptr})
                    fan.fan_id = rout[0]

                finally:
                    if speeds_ptr:
                        speeds_ptr.free()

            self.registered = True
            if self.debug_fandriverpyromaniac:
                print("Registered with FanController")

        except RISCOSError as exc:
            if self.debug_fandriverpyromaniac:
                print("Could not register with FanController")

    def deregister(self, silent=False):
        try:
            for fan in self.fans:
                if fan.fan_id is not None:
                    try:
                        self.ro.kernel.api.swi(FanConstants.SWIFanController_Deregister,
                                               args=[fan.fan_id])
                    except Exception:
                        if not silent:
                            raise
                        # If silent, we just mark them as deregistered silently.
                fan.fan_id = None
            if self.debug_fandriverpyromaniac:
                print("Deregistered with FanController")

        except RISCOSError as exc:
            if self.debug_fandriverpyromaniac:
                print("Could not deregister with FanController")
        self.registered = False

    def initialise(self, arguments, pwp):
        self.pwp = pwp
        self.provider_name = self.ro.kernel.da_rma.strdup("Pyromaniac")
        self.register()

    def finalise(self, pwp):
        self.deregister()
        self.provider_name.free()
        self.provider_name = None

    def service(self, service_number, regs):
        if service_number == FanConstants.Service_FanControllerStarted:
            self.register()
        elif service_number == FanConstants.Service_FanControllerDying:
            self.deregister(silent=True)

    def get_fan(self, fan_id):
        """
        Look up the fan in our list by its ID.
        """
        # FIXME: Change to a dictionary?
        for fan in self.fans:
            if fan.fan_id == fan_id:
                return fan
        return None

    def driver(self, regs):
        """
        Entry point for the fan driver
        """

        reason = regs[0]
        fan_id = regs[1]
        location_id = regs[2]

        fan = self.get_fan(fan_id)
        if not fan:
            # Don't understand this request so we'll just return a failure
            regs[0] = -1
            return

        if self.debug_fandriverpyromaniac:
            print("FanDriver call for fan {!r} (location &{:08x}, reason {})".format(fan, location_id, reason))

        if reason == FanConstants.FanDriver_GetSpeed:
            regs[3] = fan.speed

        elif reason == FanConstants.FanDriver_SetSpeed:
            fan.speed = regs[3]

        elif reason == FanConstants.FanDriver_GetControlMode:
            regs[3] = fan.mode

        elif reason == FanConstants.FanDriver_SetControlMode:
            fan.mode = regs[3]

        elif reason == FanConstants.FanDriver_SetLocation:
            fan.location = regs[3]

        else:
            # Not recognised, so explicitly return a failure
            regs[0] = -1
