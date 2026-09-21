"""Battery voltage and charge estimate from the INA219 on the Waveshare JetBot board.

Standard library only, so it runs on the robot host and inside the Jupyter container.

From the robot:    python3 ~/jetbot/notebooks/mini_av/battery.py
From your PC:      ssh jetbot@<robot-ip> python3 jetbot/notebooks/mini_av/battery.py

The estimate is only valid at rest: under motor load the voltage sags, while charging it reads high.
"""

import fcntl
import os

I2C_BUS = '/dev/i2c-1'
INA219_ADDRESS = 0x41
BUS_VOLTAGE_REGISTER = 0x02
I2C_SLAVE = 0x0703  # ioctl request that selects the device address

CELLS = 3  # 3S lithium-ion pack
# resting voltage per cell -> charge in percent (typical lithium-ion curve)
CELL_CURVE = [(3.30, 0), (3.50, 6), (3.60, 15), (3.70, 30), (3.80, 48), (3.90, 65), (4.00, 79), (4.10, 90), (4.20, 100)]


def read_voltage():
    """Battery pack voltage in volts"""
    fd = os.open(I2C_BUS, os.O_RDWR)
    try:
        fcntl.ioctl(fd, I2C_SLAVE, INA219_ADDRESS)
        os.write(fd, bytes([BUS_VOLTAGE_REGISTER]))
        high, low = os.read(fd, 2)
    finally:
        os.close(fd)
    return ((high << 8 | low) >> 3) * 0.004  # 4 mV per bit, lowest 3 bits are status flags


def charge_percent(voltage):
    """Estimated charge from the resting voltage, interpolated on the cell curve"""
    cell = voltage / CELLS
    if cell <= CELL_CURVE[0][0]:
        return 0
    for (v0, p0), (v1, p1) in zip(CELL_CURVE, CELL_CURVE[1:]):
        if cell <= v1:
            return int(round(p0 + (p1 - p0) * (cell - v0) / (v1 - v0)))
    return 100


if __name__ == '__main__':
    volts = read_voltage()
    print('battery %.2f V  about %d %%  (only valid at rest: unplug the charger and wait 5 minutes)'
          % (volts, charge_percent(volts)))
