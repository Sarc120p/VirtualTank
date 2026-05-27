"""
Modbus TCP PLC Simulator (compatible with pymodbus 2.5.3).
Simulates a fermentation tank with states: Idle, Filling, Fermenting, Emptying, Cleaning.
Includes Pressure Relief Valve (PRV) on register 12.
"""
import random
import time
import threading
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext


def create_initial_block():
    return ModbusSequentialDataBlock(0, [
        200,   # 0: Temperature (20.0 C)
        1000,  # 1: Pressure (100.0 kPa)
        0,     # 2: Level (0 %)
        0,     # 3: Agitator speed (RPM)
        0,     # 4: Drain valve (0=closed)
        0,     # 5: High temperature alarm
        0,     # 6: Low pressure alarm
        0,     # 7: Batches produced
        0,     # 8: Operating time (min)
        0,     # 9: High pressure alarm
        0,     # 10: Cooling (0=off)
        0,     # 11: State (0=Idle, 1=Filling, 2=Fermenting, 3=Emptying, 4=Cleaning)
        0,     # 12: PRV - Pressure Relief Valve (0=closed, 1=open)
    ])


store = ModbusSlaveContext(hr=create_initial_block(), zero_mode=True)
context = ModbusServerContext(slaves=store, single=True)


def update_simulator():
    cleaning_cycle = 0

    while True:
        hr = context[0].getValues(3, 0, count=13)

        # Preserve externally written values
        drain_valve = context[0].getValues(3, 4, count=1)[0]
        cooling = context[0].getValues(3, 10, count=1)[0]
        state = context[0].getValues(3, 11, count=1)[0]
        agitator_speed = context[0].getValues(3, 3, count=1)[0]
        prv = context[0].getValues(3, 12, count=1)[0]

        hr[4] = drain_valve
        hr[10] = cooling
        hr[11] = state
        hr[3] = agitator_speed
        hr[12] = prv

        # --- State machine ---
        if state == 0:  # Idle
            hr[0] = max(180, hr[0] - random.randint(1, 2))
            hr[1] = max(980, hr[1] - random.randint(1, 2))
            hr[2] = max(0, hr[2] - random.randint(0, 1))
            hr[3] = max(0, hr[3] - random.randint(0, 5))
            if hr[2] <= 0:
                hr[2] = 0

        elif state == 1:  # Filling
            hr[2] = min(1000, hr[2] + random.randint(30, 50))
            hr[0] = max(180, hr[0] - random.randint(1, 2))
            hr[1] = max(980, hr[1] + random.randint(0, 1))
            if hr[2] >= 1000:
                hr[2] = 1000
                hr[11] = 2

        elif state == 2:  # Fermenting
            if cooling == 1:
                hr[0] = max(180, hr[0] - random.randint(3, 5))
            else:
                hr[0] = min(300, hr[0] + random.randint(1, 2))

            if hr[3] < 300:
                hr[1] = min(1060, hr[1] + random.randint(0, 2))
            else:
                hr[1] = min(1060, hr[1] + random.randint(1, 3))

            hr[2] = max(0, hr[2] - random.randint(0, 1))
            if hr[2] <= 0:
                hr[2] = 0
                hr[11] = 0

        elif state == 3:  # Emptying
            hr[2] = max(0, hr[2] - random.randint(40, 60))
            hr[0] = max(180, hr[0] - random.randint(1, 2))
            hr[1] = max(980, hr[1] - random.randint(2, 4))
            if hr[2] <= 0:
                hr[2] = 0
                hr[7] += 1
                hr[11] = 0

        elif state == 4:  # Cleaning
            if cleaning_cycle < 3:
                if hr[2] < 900 and not hasattr(update_simulator, 'clean_filling'):
                    update_simulator.clean_filling = True
                if hr[2] >= 900:
                    update_simulator.clean_filling = False
                if hr[2] <= 100:
                    update_simulator.clean_filling = True
                    cleaning_cycle += 1

                if getattr(update_simulator, 'clean_filling', True):
                    hr[2] = min(1000, hr[2] + random.randint(40, 60))
                else:
                    hr[2] = max(0, hr[2] - random.randint(40, 60))
            else:
                hr[2] = max(0, hr[2] - random.randint(40, 60))
                if hr[2] <= 0:
                    hr[2] = 0
                    hr[11] = 0
                    cleaning_cycle = 0

            hr[0] = max(180, hr[0] - random.randint(1, 2))
            hr[1] = max(980, hr[1] - random.randint(1, 2))

        # --- PRV (register 12) ---
        if prv == 1:
            hr[1] = max(980, hr[1] - random.randint(5, 10))

        # --- Alarms ---
        hr[5] = 1 if hr[0] > 280 else 0
        hr[6] = 1 if hr[1] < 990 else 0
        hr[9] = 1 if hr[1] > 1050 else 0

        # --- Elapsed time ---
        hr[8] += 1

        context[0].setValues(3, 0, hr)
        time.sleep(2)


update_simulator.clean_filling = True

thread = threading.Thread(target=update_simulator, daemon=True)
thread.start()


if __name__ == "__main__":
    print("[OK] PLC Simulator started at localhost:5020")
    print("     States: 0=Idle 1=Filling 2=Fermenting 3=Emptying 4=Cleaning")
    print("     PRV on register 12 (0=closed, 1=open)")
    print("     (Ctrl+C to stop)")

    try:
        StartTcpServer(context, address=("127.0.0.1", 5020))
    except KeyboardInterrupt:
        print("\n[OK] Simulator stopped.")