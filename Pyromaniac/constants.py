"""
Constants we use for FanController
"""

class FanConstants(object):

    # Fan descriptor details
    FanType_Location_Shift = 0
    FanType_Location_Mask = 255
    FanType_Sequence_Shift = 8
    FanType_Sequence_Mask = 255
    FanType_Device_Shift = 16
    FanType_Device_Mask = 255

    # Fan device types
    FanType_Device_CPU = 0
    FanType_Device_GPU = 1
    FanType_Device_Memory = 2
    FanType_Device_IOCard = 3
    FanType_Device_PSU = 16
    FanType_Device_Backplane = 17
    FanType_Device_Radiator = 18
    FanType_Device_Chassis = 19
    FanType_Device_External = 32
    FanType_Device_Generic = 255

    # Fan device locations for specific devices
    FanType_Location_CPU_OnChip = 0
    FanType_Location_GPU_OnChip = 0
    FanType_Location_Memory_OnModule = 0
    FanType_Location_Memory_OnCPUBank = 1
    FanType_Location_Memory_OnChannel = 2
    FanType_Location_Memory_OnRiser = 3
    FanType_Location_IOCard_OnCard = 0
    FanType_Location_Space_LateralUnspecified = 0
    FanType_Location_Space_LateralLeft = 1
    FanType_Location_Space_LateralMiddle = 2
    FanType_Location_Space_LateralRight = 3
    FanType_Location_Space_LateralShift = 0
    FanType_Location_Space_LateralMask = 3
    FanType_Location_Space_LongitudinalUnspecified = 0
    FanType_Location_Space_LongitudinalFront = 1
    FanType_Location_Space_LongitudinalMiddle = 2
    FanType_Location_Space_LongitudinalRear = 3
    FanType_Location_Space_LongitudinalShift = 2
    FanType_Location_Space_LongitudinalMask = 3
    FanType_Location_Space_VerticalUnspecified = 0
    FanType_Location_Space_VerticalLower = 1
    FanType_Location_Space_VerticalMiddle = 2
    FanType_Location_Space_VerticalUpper = 3
    FanType_Location_Space_VerticalShift = 4
    FanType_Location_Space_VerticalMask = 3
    FanType_Location_Space_Unspecified = 255
    FanType_Location_External_UPS = 0
    FanType_Location_External_ExternalDrive = 1
    FanType_Location_External_ExternalDevice = 2
    FanType_Location_External_DeskFan = 64
    FanType_Location_External_Aircon = 65
    FanType_Location_External_PizzaOven = 254
    FanType_Location_External_Unspecified = 255

    # Fan speed
    FanSpeed_Accuracy_Unknown = 0

    # Fan capabilties:
    FanCapability_SupportsManual = (1<<0)
    FanCapability_SupportsAutomatic = (1<<1)
    FanCapability_SupportsMove = (1<<2)
    FanCapability_CanFail = (1<<3)
    FanCapability_Type_Fan = 0
    FanCapability_Type_Piezoelectric = 1
    FanCapability_Type_Peltier = 2
    FanCapability_Type_Liquid = 3
    FanCapability_Type_Shift = 28
    FanCapability_Type_Mask = 15

    # Fan state
    FanState_OK = 0
    FanState_Disconnected = -1
    FanState_Failed = -2

    # Driver operations
    FanDriver_GetSpeed = 0
    FanDriver_SetSpeed = 1
    FanDriver_GetControlMode = 2
    FanDriver_SetControlMode = 3
    FanDriver_SetLocation = 4

    # Configuration of the fan control
    FanControl_Manual = 0
    FanControl_AutomaticPerformance = 1
    FanControl_AutomaticNoise = 2

    # Location change response
    FanSetLocation_OK = 0
    FanSetLocation_Invalid = 1

    # FanController_Configure reasons
    FanController_Configure_Control = 0
    FanController_Configure_Location = 1

    # Service calls - NOT registered
    Service_FanControllerStarted = 0x10040
    Service_FanControllerDying = 0x10041
    Service_FanControllerFanChanged = 0x10042
    Service_FanControllerFanChanged_Removed = 0
    Service_FanControllerFanChanged_Added = 1
    Service_FanControllerFanChangedState = 0x10043

    # Error numbers - NOT registered
    ErrorBase_FanController = 0x10040
    ErrorNumber_BadFan = ErrorBase_FanController + 0
    ErrorNumber_BadConfigure = ErrorBase_FanController + 1
    ErrorNumber_BadControlMode = ErrorBase_FanController + 2
    ErrorNumber_RegisterFailed = ErrorBase_FanController + 3
    ErrorNumber_InitFailed = ErrorBase_FanController + 4
    ErrorNumber_CannotSetSpeed = ErrorBase_FanController + 16
    ErrorNumber_CannotSetLocation = ErrorBase_FanController + 17

    # SWI numbers
    SWIFanController_0 = 0x10080
    SWIFanController_Version = SWIFanController_0 + 0
    SWIFanController_Enumerate = SWIFanController_0 + 1
    SWIFanController_Info = SWIFanController_0 + 2
    SWIFanController_Speed = SWIFanController_0 + 3
    SWIFanController_Configure = SWIFanController_0 + 4
    SWIFanController_Register = SWIFanController_0 + 16
    SWIFanController_Deregister = SWIFanController_0 + 17
