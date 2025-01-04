import requests
import xml.etree.ElementTree as ET
import time
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio
from collections import Counter

# Initialize I2C and PCA9685
i2c_bus = busio.I2C(SCL, SDA)
b0 = PCA9685(i2c_bus, address=0x40)
b1 = PCA9685(i2c_bus, address=0x41)
b2 = PCA9685(i2c_bus, address=0x42)

b0.frequency = 1000
b1.frequency = 1000
b2.frequency = 1000

# Station mappings
b0_ports = {"BSR": 0, "ARZ": 1, "ETX": 2, "BOL": 3, "BAS": 4, "SAN": 5, "CAV": 6, "ABA": 7, "MOY": 8, "IND": 9, "SAM": 10, "DEU": 11, "SAR": 12, "SIN": 13, "LUT": 14, "ERA": 15}
b1_ports = {"AST": 0, "LEI": 1, "LAM": 2, "ARE": 3, "GOB": 4, "NEG": 5, "AIB": 6, "ALG": 7, "BID": 8, "IBB": 9, "BER": 10, "LAR": 11, "SOP": 12, "URD": 13, "PLE": 14, "GUR": 15}
b2_ports = {"ANS": 0, "BAR": 1, "BAG": 2, "URB": 3, "SES": 4, "ABT": 5, "POR": 6, "PEN": 7, "STZ": 8, "KAB": 9, "ON": 10, "API": 11}

active_stations = set()
blinking_stations = set()

# Fetch vehicle positions from API
def get_vehicle_positions():
    url = "https://ctb-siri.s3.eu-south-2.amazonaws.com/metro-bilbao-vehicle-positions.xml"
    response = requests.get(url)
    positions = []

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        ns = {'siri': 'http://www.siri.org.uk/siri'}
        for vehicle in root.findall(".//siri:VehicleActivity", ns):
            try:
                vehicle_id = vehicle.find(".//siri:VehicleRef", ns).text
                station_ref = vehicle_id.split('_')[0]  # Extract station from VehicleRef
                positions.append(station_ref)
                print(f"Train at Station: {station_ref}")
            except AttributeError:
                print("Error parsing vehicle entry.")
    else:
        print(f"Error accessing XML feed: {response.status_code}")

    return positions

# Control LEDs based on station

def control_leds(stations):
    global active_stations, blinking_stations
    station_counts = Counter(stations)

    # Turn off LEDs for stations that are no longer active
    for station in active_stations - set(stations):
        if station in b0_ports:
            b0.channels[b0_ports[station]].duty_cycle = 0
        elif station in b1_ports:
            b1.channels[b1_ports[station]].duty_cycle = 0
        elif station in b2_ports:
            b2.channels[b2_ports[station]].duty_cycle = 0
        print(f"{station} LED OFF")

    # Turn on or blink LEDs for active stations
    for station, count in station_counts.items():
        if station in b0_ports or station in b1_ports or station in b2_ports:
            if count > 1:
                blinking_stations.add(station)
            else:
                blinking_stations.discard(station)
                if station in b0_ports:
                    b0.channels[b0_ports[station]].duty_cycle = 65535
                elif station in b1_ports:
                    b1.channels[b1_ports[station]].duty_cycle = 65535
                elif station in b2_ports:
                    b2.channels[b2_ports[station]].duty_cycle = 65535
                print(f"{station} LED ON")

    active_stations = set(stations)

# Blink LEDs for stations with multiple trains

def blink_leds():
    while True:
        for station in blinking_stations:
            if station in b0_ports:
                b0.channels[b0_ports[station]].duty_cycle = 65535
            elif station in b1_ports:
                b1.channels[b1_ports[station]].duty_cycle = 65535
            elif station in b2_ports:
                b2.channels[b2_ports[station]].duty_cycle = 65535
        time.sleep(0.5)
        for station in blinking_stations:
            if station in b0_ports:
                b0.channels[b0_ports[station]].duty_cycle = 0
            elif station in b1_ports:
                b1.channels[b1_ports[station]].duty_cycle = 0
            elif station in b2_ports:
                b2.channels[b2_ports[station]].duty_cycle = 0
        time.sleep(0.5)

# Run power-on sequence

def run_power_on_sequence():
    for step in sequence:
        control_leds(step)
        time.sleep(0.2)

# Turn on ON and API LEDs
b2.channels[b2_ports["ON"]].duty_cycle = 65535
b2.channels[b2_ports["API"]].duty_cycle = 0

sequence = [
    ["PLE"], ["URD"], ["SOP"], ["LAR"], ["BER"], ["IBB"],
    ["BID", "KAB"], ["ALG", "STZ"], ["AIB", "PEN"], ["NEG", "POR"],
    ["GOB", "ABT"], ["ARE", "SES"], ["LAM", "URB"], ["LEI", "BAG"],
    ["AST", "BAR"], ["ERA", "ANS"], ["LUT", "GUR"], ["SIN"], ["SAR"],
    ["DEU"], ["SAM"], ["IND"], ["MOY"], ["ABA"], ["CAV"], ["SAN"],
    ["BAS"], ["BOL"], ["ETX"], ["ARZ"], ["BSR"]
]

if __name__ == "__main__":
    try:
        run_power_on_sequence()

        from threading import Thread
        blink_thread = Thread(target=blink_leds, daemon=True)
        blink_thread.start()

        while True:
            new_active_stations = get_vehicle_positions()
            if not new_active_stations:
                b2.channels[b2_ports["API"]].duty_cycle = 65535
                run_power_on_sequence()
            else:
                b2.channels[b2_ports["API"]].duty_cycle = 0
                control_leds(new_active_stations)
            time.sleep(30)
    except KeyboardInterrupt:
        print("Shutting down...")
        control_leds([])
        b0.deinit()
        b1.deinit()
        b2.deinit()
