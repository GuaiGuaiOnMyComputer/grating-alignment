#!/usr/bin/env python3
"""
GPIO Pin Discovery Tool for Jetson Orin Nano
Tests which GPIO pins are available and valid for use
"""

import Jetson.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common GPIO pin ranges for Jetson Orin Nano (BOARD numbering)
# These are the most commonly used GPIO pins
GPIO_PIN_RANGES = [
    # Main GPIO header pins (physical pin numbers)
    [7, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40],
    # Extended range for testing
    list(range(1, 41))
]

def test_gpio_pin(pin):
    """Test if a GPIO pin is valid and can be used"""
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.01)  # Brief pulse
        GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup(pin)  # Clean up this pin
        return True, "OK"
    except Exception as e:
        return False, str(e)

def discover_valid_pins():
    """Discover all valid GPIO pins"""
    logger.info("Starting GPIO pin discovery...")
    logger.info("Testing common GPIO pin ranges...")

    valid_pins = []
    invalid_pins = []

    # Test the most common pins first
    for pin in GPIO_PIN_RANGES[0]:
        is_valid, status = test_gpio_pin(pin)
        if is_valid:
            valid_pins.append(pin)
            logger.info(f"✓ Pin {pin}: Valid - {status}")
        else:
            invalid_pins.append((pin, status))
            logger.warning(f"✗ Pin {pin}: Invalid - {status}")

    # If we found enough valid pins, stop here
    if len(valid_pins) >= 5:
        logger.info(f"Found {len(valid_pins)} valid GPIO pins")
        return valid_pins, invalid_pins

    # Otherwise test the full range
    logger.info("Testing full pin range (1-40)...")
    for pin in GPIO_PIN_RANGES[1]:
        if pin in valid_pins or pin in [p[0] for p in invalid_pins]:
            continue  # Already tested

        is_valid, status = test_gpio_pin(pin)
        if is_valid:
            valid_pins.append(pin)
            logger.info(f"✓ Pin {pin}: Valid - {status}")
        else:
            invalid_pins.append((pin, status))
            logger.debug(f"✗ Pin {pin}: Invalid - {status}")

    logger.info(f"Discovery complete. Found {len(valid_pins)} valid GPIO pins")
    return valid_pins, invalid_pins

def test_led_pins():
    """Test common LED pin locations"""
    logger.info("Testing common LED pin locations...")

    # Common LED pins for different Jetson models
    led_pin_candidates = {
        'Jetson Orin Nano': [33, 24, 50],
        'Jetson Orin NX': [24, 33],
        'Jetson Xavier NX': [33, 24],
        'Jetson Nano': [33, 50]
    }

    working_leds = {}

    for model, pins in led_pin_candidates.items():
        logger.info(f"Testing {model} LED pins: {pins}")
        for pin in pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.5)
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(pin, GPIO.LOW)
                GPIO.cleanup(pin)
                working_leds[model] = pin
                logger.info(f"✓ {model} LED pin {pin}: Working")
                break  # Found one, move to next model
            except Exception as e:
                logger.debug(f"✗ {model} LED pin {pin}: {e}")

    return working_leds

def main():
    """Main discovery function"""
    logger.info("=== Jetson Orin GPIO Pin Discovery Tool ===")

    try:
        GPIO.setmode(GPIO.BOARD)

        # Discover valid GPIO pins
        valid_pins, invalid_pins = discover_valid_pins()

        logger.info("\n" + "="*50)
        logger.info("VALID GPIO PINS:")
        logger.info(f"Found {len(valid_pins)} valid pins: {valid_pins}")

        logger.info("\nINVALID GPIO PINS:")
        logger.info(f"Found {len(invalid_pins)} invalid pins:")
        for pin, error in invalid_pins[:10]:  # Show first 10
            logger.info(f"  Pin {pin}: {error}")
        if len(invalid_pins) > 10:
            logger.info(f"  ... and {len(invalid_pins) - 10} more")

        # Test LED pins
        logger.info("\n" + "="*50)
        working_leds = test_led_pins()

        logger.info("\n" + "="*50)
        logger.info("LED PIN RESULTS:")
        if working_leds:
            for model, pin in working_leds.items():
                logger.info(f"✓ {model}: LED pin {pin}")
        else:
            logger.warning("No working LED pins found")

        # Recommendations
        logger.info("\n" + "="*50)
        logger.info("RECOMMENDATIONS:")
        if valid_pins:
            logger.info(f"For GPIO pins 1,2: Try {valid_pins[:2]} instead")
            if len(valid_pins) >= 3:
                logger.info(f"For LED: Try pin {valid_pins[2]} or check board documentation")

        logger.info("\nDiscovery completed!")

    except Exception as e:
        logger.error(f"Error during discovery: {e}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()



