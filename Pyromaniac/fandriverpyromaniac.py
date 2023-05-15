"""
A very rudimentary fan driver.
"""

from pyromaniac.config import Configuration, ConfigurationError

from riscos.errors import RISCOSSyntheticError, RISCOSError
from riscos.modules.pymodules import PyModule

from .constants import FanConstants

FanTechMapping = {
        'fan': FanConstants.FanCapability_Type_Fan,
        'piezoelectric': FanConstants.FanCapability_Type_Piezoelectric,
        'peltier': FanConstants.FanCapability_Type_Peltier,
        'liquid': FanConstants.FanCapability_Type_Liquid,
    }
FanPosLateralMapping = {
        'unspecified': FanConstants.FanType_Location_Space_LateralUnspecified,
        'left': FanConstants.FanType_Location_Space_LateralLeft,
        'middle': FanConstants.FanType_Location_Space_LateralMiddle,
        'right': FanConstants.FanType_Location_Space_LateralRight,
    }
FanPosLongitudinalMapping = {
        'unspecified': FanConstants.FanType_Location_Space_LongitudinalUnspecified,
        'front': FanConstants.FanType_Location_Space_LongitudinalFront,
        'middle': FanConstants.FanType_Location_Space_LongitudinalMiddle,
        'rear': FanConstants.FanType_Location_Space_LongitudinalRear,
    }
FanPosVerticalMapping = {
        'unspecified': FanConstants.FanType_Location_Space_VerticalUnspecified,
        'lower': FanConstants.FanType_Location_Space_VerticalLower,
        'middle': FanConstants.FanType_Location_Space_VerticalMiddle,
        'upper': FanConstants.FanType_Location_Space_VerticalUpper,
    }
DeviceMapping = {
        'cpu': FanConstants.FanType_Device_CPU,
        'gpu': FanConstants.FanType_Device_GPU,
        'memory': FanConstants.FanType_Device_Memory,
        'iocard': FanConstants.FanType_Device_IOCard,
        'psu': FanConstants.FanType_Device_PSU,
        'backplane': FanConstants.FanType_Device_Backplane,
        'radiator': FanConstants.FanType_Device_Radiator,
        'chassis': FanConstants.FanType_Device_Chassis,
        'external': FanConstants.FanType_Device_External,
        'generic': FanConstants.FanType_Device_Generic,
    }

def SpeedList(value):
    if not value:
        return []
    def convert(v):
        try:
            return int(v)
        except Exception as exc:
            raise ConfigurationError("SpeedList should contain a comma-separated list of speeds (%s)" % (exc,))
    return [convert(part) for part in value.split(',')]
SpeedList.format = lambda value: ','.join('%i' % (part,) for part in value)
SpeedList.help = "Comma separated list of speeds, or empty for arbitrary speeds"


class FanDriverConfig(Configuration):
    _types = {
            'speeds': SpeedList,
            'accuracy': int,
            'max_speed': int,
            'capabilities': 'flags:manual,auto,moveable,can-fail',
            'tech': 'enum:fan,piezoelectric,peltier,liquid',
            'position_lateral': 'enum:unspecified,left,middle,right',
            'position_longitudinal': 'enum:unspecified,front,middle,rear',
            'position_vertical': 'enum:unspecified,lower,middle,upper',
            'device': 'enum:cpu,gpu,memory,iocard,psu,backplane,radiator,chassis,external,generic'
    }
    _help = {
            'fan_speeds': """
Configures the list of speeds supported by the FanDriver. If the list
is empty, no fan speed restrictions will be reported.
""",

            'accuracy': """
Configures the accuracy of the speed that can be selected by the fan.
""",

            'max_speed': """
Configures the maximum speed supported by the fan, or 0 for no explicit
maximum.
""",

            'capabilities': """
Configures the capabilities of the fan as a comma-separated set of flags.
The recognised flags are:

    * `manual` - fan supports manual speed selection.
    * `auto` - fan support automatic speed selection.
    * `moveable` - fan can have its location changed.
    * `can-fail` - fan can report that it has failed.
""",

            'tech': """
Configures the technology of the cooling device that the 'fan' is provided by.
The recognised technology types are:

    * `fan`
    * `piezoelectric`
    * `peltier`
    * `liquid`
""",

            'device': """
Configures the logical device cooled by the fan.
Some of the devices have spacial qualifiers which position the device more
specifically (see `position_lateral`, `position_longitudinal`, and
`position_vertical`). Some devices have different position qualifiers.
The recognised devices are:

    * `CPU`
    * `GPU`
    * `Memory`
    * `IOCard`
    * `PSU`
    * `Backplane`
    * `Radiator`
    * `Chassis`
    * `External`
    * `Generic`
""",

            'position_lateral': """
Configures the logical position of the fan device, in lateral (left-to-right)
space. This configuration only applies to devices that are spacially
distinguished. The recognised positions are:

    * `unspecified`
    * `left`
    * `middle`
    * `right`
""",

            'position_longitudinal': """
Configures the logical position of the fan device, in longitudal
(front-to-rear) space. This configuration only applies to devices that are
spacially distinguished. The recognised positions are:

    * `unspecified`
    * `front`
    * `middle`
    * `rear`
""",

            'position_vertical': """
Configures the logical position of the fan device, in vertical
(bottom-to-top) space. This configuration only applies to devices that are
spacially distinguished. The recognised positions are:

    * `unspecified`
    * `lower`
    * `middle`
    * `upper`
""",
    }
    speeds = []
    accuracy = 10
    max_speed = 0
    capabilities = (FanConstants.FanCapability_SupportsManual |
                    FanConstants.FanCapability_SupportsAutomatic)
    tech = 'fan'
    position_lateral = 'left'
    position_longitudinal = 'rear'
    position_vertical = 'unspecified'
    device = 'chassis'


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
    version = '0.02'
    date = '17 Jan 2022'

    entrypoint_names = [
            'driver',
        ]

    def __init__(self, ro, module):
        super(FanDriverPyromaniac, self).__init__(ro, module)
        self.registered = False
        self.pwp = None
        self.provider_name = None

        location_id = DeviceMapping[self.ro.config['fandriver.device']]<<FanConstants.FanType_Device_Shift
        if 16 <= DeviceMapping[self.ro.config['fandriver.device']] < 32:
            # Positional device
            location_id |= ((FanPosLateralMapping[self.ro.config['fandriver.position_lateral']]<<FanConstants.FanType_Location_Space_LateralShift) |
                            (FanPosLongitudinalMapping[self.ro.config['fandriver.position_longitudinal']]<<FanConstants.FanType_Location_Space_LongitudinalShift) |
                            (FanPosVerticalMapping[self.ro.config['fandriver.position_vertical']]<<FanConstants.FanType_Location_Space_VerticalShift)) << FanConstants.FanType_Location_Shift
        else:
            # FIXME: Other configured locations
            pass
        # FIXME: Configurable sequence?
        location_id |= (0<<FanConstants.FanType_Sequence_Shift)

        # The fans that we'll declare
        self.fans = [
                Fan(location_id=location_id,
                    speeds=self.ro.config['fandriver.speeds'] or None,
                    accuracy=self.ro.config['fandriver.accuracy'],
                    maximum=self.ro.config['fandriver.max_speed'],
                    capabilities=(self.ro.config['fandriver.capabilities'] |
                                  FanTechMapping[self.ro.config['fandriver.tech']] << FanConstants.FanCapability_Type_Shift))
            ]

        self.debug_fandriverpyromaniac = False
        self.ro.debug_register_ivar('fandriverpyromaniac', self)

    def register(self):
        if self.registered:
            return

        try:
            for fan in self.fans:
                try:
                    speeds_ptr = 0
                    if fan.speeds:
                        speeds_ptr = self.ro.kernel.da_rma.allocate(4 * (len(fan.speeds) + 1))
                        speeds_ptr.write_words(fan.speeds)
                        speeds_ptr[4 * len(fan.speeds)].word = -1

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
            fan.location_id = regs[3]
            regs[3] = FanConstants.FanSetLocation_OK

        else:
            # Not recognised, so explicitly return a failure
            regs[0] = -1
