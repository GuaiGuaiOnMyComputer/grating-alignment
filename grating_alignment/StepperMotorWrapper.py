import asyncio
import threading
from typing import List
from logging import Formatter, Handler
from typing import Optional
from tmc_driver.tmc_220x import Tmc220x, MovementAbsRel, StopMode, MovementAbsRel, DrvStatus, GConf, GStat, Ioin, ChopConf, Loglevel
from tmc_driver.tmc_2209 import Tmc2209, TmcComUart, TmcEnableControlPin, TmcMotionControlStepDir

class Tmc2209StepperWrapperFactory():

    @staticmethod
    def create(
            enable_pin: int, 
            step_signal_pin: int, 
            step_direction_pin: int, 
            com_uart:str | None = None, 
            log_prefix = "TMC2209-Stepper", 
            log_formatter: Formatter | None = None, 
            log_handler: List[Handler] | None = None
        ):
        """Create a Tmc220xStepperWrapper.
        
        Args:
            enable_pin (int): The pin number for the enable signal.
            step_signal_pin (int): The pin number for the step signal.
            step_direction_pin (int): The pin number for the direction signal.
            com_uart (str | None): The UART port to use for communication.
            log_prefix (str): The prefix for the logger.
            log_formatter (Formatter | None): The formatter for the logger.
            log_handler (List[Handler] | None): The handlers for the logger.
        """

        enable_control_poin:TmcMotionControlStepDir = TmcEnableControlPin(enable_pin)
        motion_control_step_dir: TmcMotionControlStepDir = TmcMotionControlStepDir(step_signal_pin, step_direction_pin)
        motor_com_uart: TmcComUart | None = TmcComUart(com_uart) if com_uart is not None else None

        tmc_stepper: Tmc2209 = Tmc2209(enable_control_poin, motion_control_step_dir, motor_com_uart, logprefix = log_prefix, log_formatter = log_formatter, log_handlers = log_handler)
        return Tmc220xStepperWrapper(tmc_stepper)


class Tmc220xStepperWrapper:
    """Async adapter for Tmc220x blocking operations."""

    def __init__(self, stepper: Tmc220x):
        """Initialize the Tmc220xStepperWrapper.
        
        Args:
            stepper (Tmc220x): The Tmc220x instance to wrap.
        """

        if not isinstance(stepper, Tmc220x):
            raise ValueError("Stepper must inherit from Tmc220x.")

        self.__stepper: Tmc220x = stepper
        self.__emergency_stop_thread: Optional[threading.Thread] = None
        self.__emergency_stop_event: threading.Event = threading.Event()
        self.__emergency_stop_running: bool = False
        self.__emergency_stop_lock: threading.Lock = threading.Lock()

    def emergency_stop(self):
        """Emergency stop the stepper. And set the motor enabled to False."""
        self.__stepper.tmc_mc.stop(stop_mode = StopMode.HARDSTOP)
        self.__stepper.set_motor_enabled(False)
    
    def start_emergency_stop_thread(self):
        """Start the emergency stop monitoring thread."""
        self.__stepper.logger.info("Starting emergency stop thread. Call trigger_emergency_stop to trigger the emergency stop.")

        with self.__emergency_stop_lock:

            if not self.__emergency_stop_running:
                self.__emergency_stop_running = True
                self.__emergency_stop_thread = threading.Thread(
                    target=self.__emergency_stop_thread_worker,
                    name="EmergencyStopThread",
                    daemon=True
                )
                self.__emergency_stop_thread.start()
    
    def trigger_emergency_stop(self):
        """Trigger an emergency stop event."""
        self.__stepper.tmc_logger.log("Emergency stop event triggered.", Loglevel.ERROR)
        self._emergency_stop_event.set()
    
    def is_emergency_stop_thread_running(self) -> bool:
        """Check if the emergency stop thread is running."""
        with self.__emergency_stop_lock:
            return self.__emergency_stop_running and self.__emergency_stop_thread is not None and self.__emergency_stop_thread.is_alive()
    
    def __del__(self):
        """Destructor to ensure emergency stop thread is properly stopped."""
        self.__stop_emergency_stop_thread(True)
    
    def set_motor_enabled(self, enabled: bool):
        """Set the motor enabled.
        
        Args:
            enabled (bool): True to enable the motor, False to disable the motor.
        """
        self.__stepper.set_motor_enabled(enabled)
    
    # Tmc220x methods
    # ----------------------------
    def read_steps_per_rev(self) -> int:
        """returns how many steps are needed for one revolution.
        this reads the value from the tmc driver.

        Returns:
            int: Steps per revolution
        """
        return self.__stepper.read_steps_per_rev()

    def read_drv_status(self) -> DrvStatus:
        """read the register Adress "DRV_STATUS" and logs the reg valuess

        Returns:
            DRV_STATUS Register instance
        """
        return self.__stepper.read_drv_status()

    def read_gconf(self) -> GConf:
        """read the register Adress "GCONF" and logs the reg values

        Returns:
            GCONF Register instance
        """
        return self.__stepper.read_gconf()

    def read_gstat(self) -> GStat:
        """read the register Adress "GSTAT" and logs the reg values

        Returns:
            GSTAT Register instance
        """
        return self.__stepper.read_gstat()

    def clear_gstat(self):
        """clears the "GSTAT" register"""
        self.__stepper.clear_gstat()

    def read_ioin(self) -> Ioin:
        """read the register Adress "IOIN" and logs the reg values

        Returns:
            IOIN Register instance
        """
        return self.__stepper.read_ioin()

    def read_chopconf(self) -> ChopConf:
        """read the register Adress "CHOPCONF" and logs the reg values

        Returns:
            CHOPCONF Register instance
        """
        return self.__stepper.read_chopconf()

    def get_direction_reg(self) -> bool:
        """returns the motor shaft direction: False = CCW; True = CW

        Returns:
            bool: motor shaft direction: False = CCW; True = CW
        """
        return self.__stepper.get_direction_reg()

    def set_direction_reg(self, direction:bool):
        """sets the motor shaft direction to the given value: False = CCW; True = CW

        Args:
            direction (bool): direction of the motor False = CCW; True = CW
        """
        self.__stepper.set_direction_reg(direction)

    def get_iscale_analog(self) -> bool:
        """return whether Vref (True) or 5V (False) is used for current scale

        Returns:
            en (bool): whether Vref (True) or 5V (False) is used for current scale
        """
        return self.__stepper.get_iscale_analog()

    def set_iscale_analog(self,en:bool):
        """sets Vref (True) or 5V (False) for current scale

        Args:
            en (bool): True=Vref, False=5V
        """
        self.__stepper.set_iscale_analog(en)

    def get_vsense(self) -> bool:
        """returns which sense resistor voltage is used for current scaling
        False: Low sensitivity, high sense resistor voltage
        True: High sensitivity, low sense resistor voltage

        Returns:
            bool: whether high sensitivity should is used
        """
        return self.__stepper.get_vsense()

    def set_vsense(self,en:bool):
        """sets which sense resistor voltage is used for current scaling
        False: Low sensitivity, high sense resistor voltage
        True: High sensitivity, low sense resistor voltage

        Args:
            en (bool):
        """
        self.__stepper.set_vsense(en)

    def get_internal_rsense(self) -> bool:
        """returns which sense resistor voltage is used for current scaling
        False: Operation with external sense resistors
        True Internal sense resistors. Use current supplied into
        VREF as reference for internal sense resistor. VREF
        pin internally is driven to GND in this mode.

        Returns:
            bool: which sense resistor voltage is used
        """
        return self.__stepper.get_internal_rsense()

    def set_internal_rsense(self,en:bool):
        """sets which sense resistor voltage is used for current scaling
        False: Operation with external sense resistors
        True: Internal sense resistors. Use current supplied into
        VREF as reference for internal sense resistor. VREF
        pin internally is driven to GND in this mode.

        Args:
        en (bool): which sense resistor voltage is used; true will propably destroy your tmc

            """
        self.__stepper.set_internal_rsense(en)

    def set_current(self, run_current:int, hold_current_multiplier:float = 0.5,
                    hold_current_delay:int = 10, pdn_disable:bool = True):
        """sets the current flow for the motor.

        Args:
        run_current (int): current during movement in mA
        hold_current_multiplier (int):current multiplier during standstill (Default value = 0.5)
        hold_current_delay (int): delay after standstill after which cur drops (Default value = 10)
        pdn_disable (bool): should be disabled if UART is used (Default value = True)

        """
        self.__stepper.set_current(run_current, hold_current_multiplier, hold_current_delay, pdn_disable)

    def get_spreadcycle(self) -> bool:
        """reads spreadcycle

        Returns:
            bool: True = spreadcycle; False = stealthchop
        """
        return self.__stepper.get_spreadcycle()

    def set_spreadcycle(self,en:bool):
        """enables spreadcycle (1) or stealthchop (0)

        Args:
        en (bool): true to enable spreadcycle; false to enable stealthchop

        """
        self.__stepper.set_spreadcycle(en)

    def get_interpolation(self) -> bool:
        """return whether the tmc inbuilt interpolation is active

        Returns:
            en (bool): true if internal µstep interpolation is enabled
        """
        return self.__stepper.get_interpolation()

    def set_interpolation(self, en:bool):
        """enables the tmc inbuilt interpolation of the steps to 256 µsteps

        Args:
            en (bool): true to enable internal µstep interpolation
        """
        self.__stepper.set_interpolation(en)

    def get_toff(self) -> int:
        """returns the TOFF register value

        Returns:
            int: TOFF register value
        """
        return self.__stepper.get_toff()

    def set_toff(self, toff:int):
        """Sets TOFF register to value

        Args:
            toff (uint8_t): value of toff (must be a four-bit value)
        """
        self.__stepper.set_toff(toff)

    def read_microstepping_resolution(self) -> int:
        """returns the current native microstep resolution (1-256)
        this reads the value from the driver register

        Returns:
            int: µstep resolution
        """
        return self.__stepper.read_microstepping_resolution()

    def get_microstepping_resolution(self) -> int:
        """returns the current native microstep resolution (1-256)
        this returns the cached value from this module

        Returns:
            int: µstep resolution
        """
        return self.__stepper.get_microstepping_resolution()

    def set_microstepping_resolution(self, mres:int):
        """sets the current native microstep resolution (1,2,4,8,16,32,64,128,256)

        Args:
            mres (int): µstep resolution; has to be a power of 2 or 1 for fullstep
        """
        self.__stepper.set_microstepping_resolution(mres)

    def set_mstep_resolution_reg_select(self, en:bool):
        """sets the register bit "mstep_reg_select" to 1 or 0 depending to the given value.
        this is needed to set the microstep resolution via UART
        this method is called by "set_microstepping_resolution"

        Args:
            en (bool): true to set µstep resolution via UART
        """
        self.__stepper.set_mstep_resolution_reg_select(en)

    def get_interface_transmission_counter(self) -> int:
        """reads the interface transmission counter from the tmc register
        this value is increased on every succesfull write access
        can be used to verify a write access

        Returns:
            int: 8bit IFCNT Register
        """
        return self.__stepper.get_interface_transmission_counter()

    def get_tstep(self) -> int:
        """reads the current tstep from the driver register

        Returns:
            int: TStep time
        """
        return self.__stepper.get_tstep()

    def set_tpwmthrs(self, tpwmthrs: int):
        """sets the current tpwmthrs

        Args:
            tpwmthrs (int): value for tpwmthrs
        """
        self.__stepper.set_tpwmthrs(tpwmthrs)

    def set_vactual(self, vactual:int):
        """sets the register bit "VACTUAL" to to a given value
        VACTUAL allows moving the motor by UART control.
        It gives the motor velocity in +-(2^23)-1 [μsteps / t]
        0: Normal operation. Driver reacts to STEP input

        Args:
            vactual (int): value for VACTUAL
        """
        self.__stepper.set_vactual(vactual)

    def get_microstep_counter(self) -> int:
        """returns the current Microstep counter.
        Indicates actual position in the microstep table for CUR_A

        Returns:
            int: current Microstep counter
        """
        return self.__stepper.get_microstep_counter()

    def get_microstep_counter_in_steps(self, offset:int=0) -> int:
        """returns the current Microstep counter.
        Indicates actual position in the microstep table for CUR_A

        Args:
            offset (int): offset in steps (Default value = 0)

        Returns:
            step (int): current Microstep counter convertet to steps
        """
        return self.__stepper.get_microstep_counter_in_steps(offset)

    # Test methods
    # ----------------------------
    def test_pin(self, pin, ioin_reg_bp):
        """tests one pin

        this function checks the connection to a pin
        by toggling it and reading the IOIN register
        """

        return self.__stepper.test_pin(pin, ioin_reg_bp)

    def test_dir_step_en(self):
        """tests the EN, DIR and STEP pin

        this sets the EN, DIR and STEP pin to HIGH, LOW and HIGH
        and checks the IOIN Register of the TMC meanwhile
        """
        # test each pin on their own
        return self.__stepper.test_dir_step_en()

    def test_com(self):
        """test method"""
        return self.__stepper.test_com()

    def stop(self):
        """Stop the motor."""
        self.__stepper.tmc_mc.stop()

    def run_to_position_steps(self, steps, movement_abs_rel:MovementAbsRel = None) -> StopMode:
        """Run to target position. Blocks the code until finished or stopped from a different thread!

        Args:
            steps: The number of steps to move.
            movement_abs_rel: The absolute or relative movement.

        Returns:
            StopMode: The stop mode.
        """
        return self.__stepper.run_to_position_steps(steps, movement_abs_rel)

    def run_to_position_fullsteps(self, steps, movement_abs_rel:MovementAbsRel = None) -> StopMode:
        """Run to target position. Blocks the code until finished or stopped from a different thread!

        Args:
            steps: The number of steps to move.
            movement_abs_rel: The absolute or relative movement.

        Returns:
            StopMode: The stop mode.
        """
        return self.__stepper.run_to_position_fullsteps(steps, movement_abs_rel)

    def run_to_position_revolutions(self, revs, movement_abs_rel:MovementAbsRel = None) -> StopMode:
        """Run to target position. Blocks the code until finished or stopped from a different thread!

        Args:
            revs: The number of revolutions to move.
            movement_abs_rel: The absolute or relative movement.

        Returns:
            StopMode: The stop mode.
        """
        return self.__stepper.run_to_position_revolutions(revs, movement_abs_rel)

    async def run_to_position_steps_async(self, steps, movement_abs_rel:MovementAbsRel = None) -> StopMode:
        """
        Run to target position in a background thread and await completion.

        Args:
            steps: The number of steps to move.
            movement_abs_rel: The absolute or relative movement.

        Returns:
            StopMode: The stop mode.
        """
        return await asyncio.to_thread(self.__stepper.run_to_position_steps, steps, movement_abs_rel)

    async def run_to_position_fullsteps_async(self, steps, movement_abs_rel:MovementAbsRel = None) -> StopMode:
        """
        Run to target position in a background thread and await completion.

        Args:
            steps: The number of steps to move.
            movement_abs_rel: The absolute or relative movement.

        Returns:
            StopMode: The stop mode.
        """
        
        return await asyncio.to_thread(self.__stepper.run_to_position_fullsteps, steps, movement_abs_rel)

    async def run_to_position_revolutions_async(self, revs, movement_abs_rel:MovementAbsRel = None) -> StopMode:
        """
        Run to target position in a background thread and await completion.

        Args:
            steps: The number of steps to move.
            movement_abs_rel: The absolute or relative movement.

        Returns:
            StopMode: The stop mode.
        """

        return await asyncio.to_thread(self.__stepper.run_to_position_revolutions, revs, movement_abs_rel)

    def __stop_emergency_stop_thread(self, due_to_destructor: bool = False):
        """Stop the emergency stop monitoring thread."""
        self.__stepper.logger.info("Stopping emergency stop thread.", Loglevel.WARNING if due_to_destructor else Loglevel.INFO)

        with self.__emergency_stop_lock:
            if self.__emergency_stop_running:
                self.__emergency_stop_running = False
                self.__emergency_stop_event.set()  # Wake up the thread
        
        if self.__emergency_stop_thread and self.__emergency_stop_thread.is_alive():
            self.__emergency_stop_thread.join(timeout=1.0)

    def __emergency_stop_thread_worker(self):
        """Worker function for the emergency stop thread."""
        while self.__emergency_stop_running:

            try:
                # Wait for emergency event with timeout to allow checking running flag
                if self.__emergency_stop_event.wait(timeout = 0.05):
                    with self.__emergency_stop_lock:
                        self.emergency_stop()

            except Exception as e:
                self.emergency_stop()
                self.__stepper.logger.log(f"Error in emergency stop thread: {e}. Motor is disabled.", Loglevel.ERROR)
                raise