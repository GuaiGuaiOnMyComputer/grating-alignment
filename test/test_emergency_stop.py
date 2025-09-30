#!/usr/bin/env python3
"""
Example usage of the emergency stop functionality in Tmc220xStepperWrapper.
"""

import time
import threading
from grating_alignment.StepperMotorWrapper import Tmc2209StepperWrapperFactory
from grating_alignment.StepperMotorWrapper import Tmc220xStepperWrapper

def main():
    # Create stepper instance
    stepper = Tmc2209StepperWrapperFactory.create(
        enable_pin=10,
        step_signal_pin=11,
        step_direction_pin=12
    )
    
    # Wrap with async wrapper
    stepper_wrapper = Tmc220xStepperWrapper(stepper)
    
    # Start the emergency stop thread
    stepper_wrapper.start_emergency_stop_thread()
    
    # Simulate some work
    try:
        # Enable motor
        stepper_wrapper.set_motor_enabled(True)
        print("Motor enabled")
        
        # Simulate a long-running operation
        print("Starting long operation...")
        for i in range(10):
            print(f"Working... {i+1}/10")
            time.sleep(1)
            
            # Simulate emergency condition (e.g., sensor trigger, user input, etc.)
            if i == 5:
                print("EMERGENCY TRIGGERED!")
                stepper_wrapper.trigger_emergency_stop()
                break
        
        print("Operation completed")
        
    except KeyboardInterrupt:
        print("Interrupted by user")
        stepper_wrapper.trigger_emergency_stop()
    
    finally:
        # Stop the emergency stop thread
        stepper_wrapper.__stop_emergency_stop_thread()
        print("Emergency stop thread stopped")
        
        # Check if thread is still running
        if stepper_wrapper.is_emergency_stop_thread_running():
            print("Warning: Emergency stop thread is still running")
        else:
            print("Emergency stop thread stopped successfully")

if __name__ == "__main__":
    main()
