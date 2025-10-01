#!/usr/bin/env python3
"""
GPIO and LED Toggle Test for Jetson Orin Nano
Toggles GPIO pins 1, 2 and onboard LED every 1 second
"""

import Jetson.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GPIO Pin Configuration (Updated based on your Jetson Orin Nano)
GPIO_PINS = [7, 11]  # GPIO pins to toggle (replacing invalid pins 1, 2)
LED_PIN = 33         # Confirmed working onboard LED pin for Jetson Orin Nano

def setup_gpio():
    """Initialize GPIO pins"""
    try:
        GPIO.setmode(GPIO.BOARD)
        logger.info("GPIO mode set to BOARD numbering")

        # Setup GPIO output pins
        for pin in GPIO_PINS:
            GPIO.setup(pin, GPIO.OUT)
            logger.info(f"Set up GPIO pin {pin} as output")

        # Setup LED pin
        GPIO.setup(LED_PIN, GPIO.OUT)
        logger.info(f"Set up LED pin {LED_PIN} as output")

        # Initialize all pins to LOW
        for pin in GPIO_PINS + [LED_PIN]:
            GPIO.output(pin, GPIO.LOW)

        logger.info("All pins initialized to LOW")
        return True

    except Exception as e:
        logger.error(f"Failed to setup GPIO: {e}")
        return False

def set_high():
    """Set all pins to HIGH"""
    for pin in GPIO_PINS + [LED_PIN]:
        GPIO.output(pin, GPIO.HIGH)
        logger.info(f"Set pin {pin} to HIGH")
        
def set_low():
    """Set all pins to LOW"""
    for pin in GPIO_PINS + [LED_PIN]:
        GPIO.output(pin, GPIO.LOW)
        logger.info(f"Set pin {pin} to LOW")
        
def toggle_pins():
    """Toggle all pins between HIGH and LOW"""
    try:
        # Toggle GPIO pins
        for pin in GPIO_PINS:
            current_state = GPIO.input(pin)
            new_state = GPIO.LOW if current_state == GPIO.HIGH else GPIO.HIGH
            GPIO.output(pin, new_state)
            logger.info(f"GPIO pin {pin}: {'HIGH' if new_state == GPIO.HIGH else 'LOW'}")

        # Toggle LED
        led_state = GPIO.input(LED_PIN)
        new_led_state = GPIO.LOW if led_state == GPIO.HIGH else GPIO.HIGH
        GPIO.output(LED_PIN, new_led_state)
        logger.info(f"LED pin {LED_PIN}: {'HIGH' if new_led_state == GPIO.HIGH else 'LOW'}")

    except Exception as e:
        logger.error(f"Error toggling pins: {e}")

def cleanup_gpio():
    """Clean up GPIO resources"""
    try:
        logger.info("Cleaning up GPIO...")
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")
    except Exception as e:
        logger.error(f"Error during GPIO cleanup: {e}")

def main():
    """Main function"""
    logger.info("Starting GPIO and LED toggle test...")
    logger.info(f"Will toggle GPIO pins: {GPIO_PINS}")
    logger.info(f"LED pin: {LED_PIN}")
    logger.info("Press Ctrl+C to stop")

    if not setup_gpio():
        logger.error("Failed to setup GPIO. Exiting.")
        return

    try:
        while True:
            toggle_pins()
            time.sleep(2)  # Wait 1 second

        # set_low()
        # logger.info("Set all pins to LOW")
        # while True:
        #     time.sleep(1)

        # set_high()
        # logger.info("Set all pins to HIGH")
        # while True:
        #     time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Stopping...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        cleanup_gpio()
        logger.info("Test completed")

if __name__ == "__main__":
    main()
