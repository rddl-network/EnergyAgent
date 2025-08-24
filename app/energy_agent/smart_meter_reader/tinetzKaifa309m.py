import serial
import time
import json
from Crypto.Cipher import AES
from datetime import datetime
from binascii import unhexlify

class TinetzKaifa309MReader:
    def __init__(self, serial_port="/dev/ttyUSB0", baud_rate=2400, address=1, decryption_key=None):
        self.key = unhexlify(decryption_key)
        self.port = serial.Serial(
            port=serial_port,
            baudrate=baud_rate,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        self.obis_codes = {
            'timestamp': '0000010000ff',
            'meter_serial_number': '0000600100ff',
            'logical_device_name': '00002a0000ff',
            'l1_voltage': '0100200700ff',
            'l2_voltage': '0100340700ff',
            'l3_voltage': '0100480700ff',
            'l1_current': '01001f0700ff',
            'l2_current': '0100330700ff',
            'l3_current': '0100470700ff',
            'power_in': '0100010700ff',
            'power_out': '0100020700ff',
            'absolute_energy_in': '0100010800ff',
            'absolute_energy_out': '0100020800ff',
            'reactive_energy_in': '0100030800ff',
            'reactive_energy_out': '0100040800ff'
        }
    

    def read_data(self):
        while True:
            data = self.port.read_all()
            if data:
                return data
            time.sleep(6)
    
    def decrypt_message(self, data):
        if len(data) < 355 or data[:4].hex() != "68fafa68":
            return None
            
        msg1_len = data[1]
        msg2_len = data[msg1_len + 7]
        
        system_title = data[11:19]
        init_counter = data[23:27]
        init_vector = system_title + init_counter
        
        msg1 = data[27:6 + msg1_len - 2]
        msg2 = data[msg1_len + 15:msg1_len + 10 + msg2_len]
        encrypted = msg1 + msg2
        
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=init_vector)
        return cipher.decrypt(encrypted).hex()
    
    def extract_value(self, data, code):
        pos = data.find(code)
        if pos < 0:
            return None
        return pos + 12
    
    def parse_timestamp(self, data):
        pos = self.extract_value(data, self.obis_codes['timestamp'])
        if not pos:
            return None
            
        raw = data[pos + 4:pos + 28]
        dt = datetime(
            int(raw[:4], 16),
            int(raw[4:6], 16),
            int(raw[6:8], 16),
            int(raw[10:12], 16),
            int(raw[12:14], 16),
            int(raw[14:16], 16)
        )
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    
    def parse_text(self, data, code):
        pos = self.extract_value(data, code)
        if not pos:
            return None
            
        length = int(data[pos + 2:pos + 4], 16) * 2
        hex_text = data[pos + 4:pos + 4 + length]
        return bytes.fromhex(hex_text).decode("ASCII")
    
    def parse_number(self, data, code, length, divisor):
        pos = self.extract_value(data, code)
        if not pos:
            return None
            
        hex_val = data[pos + 2:pos + 2 + length]
        return int(hex_val, 16) / divisor
    
    def process_meter_data(self):
        decrypted = None
        while not decrypted:
            data = self.read_data()
            decrypted = self.decrypt_message(data)
            self.port.flushInput()
            time.sleep(0.5)

        readings = {}
        
        # Basic info
        readings['timestamp'] = self.parse_timestamp(decrypted)
        readings['meter_serial_number'] = self.parse_text(decrypted, self.obis_codes['meter_serial_number'])
        readings['logical_device_name'] = self.parse_text(decrypted, self.obis_codes['logical_device_name'])
        
        # Voltages
        readings['l1_voltage'] = self.parse_number(decrypted, self.obis_codes['l1_voltage'], 4, 10)
        readings['l2_voltage'] = self.parse_number(decrypted, self.obis_codes['l2_voltage'], 4, 10)
        readings['l3_voltage'] = self.parse_number(decrypted, self.obis_codes['l3_voltage'], 4, 10)

        # Currents
        readings['l1_current'] = self.parse_number(decrypted, self.obis_codes['l1_current'], 4, 100)
        readings['l2_current'] = self.parse_number(decrypted, self.obis_codes['l2_current'], 4, 100)
        readings['l3_current'] = self.parse_number(decrypted, self.obis_codes['l3_current'], 4, 100)

        # Power & Energy
        readings['power_in'] = self.parse_number(decrypted, self.obis_codes['power_in'], 8, 1000)
        readings['power_out'] = self.parse_number(decrypted, self.obis_codes['power_out'], 8, 1000)
        readings['absolute_energy_in'] = self.parse_number(decrypted, self.obis_codes['absolute_energy_in'], 8, 1000)
        readings['absolute_energy_out'] = self.parse_number(decrypted, self.obis_codes['absolute_energy_out'], 8, 1000)
        readings['reactive_energy_in'] = self.parse_number(decrypted, self.obis_codes['reactive_energy_in'], 8, 1000)
        readings['reactive_energy_out'] = self.parse_number(decrypted, self.obis_codes['reactive_energy_out'], 8, 1000)

        return readings
    
    def read_frame(self):
        try:
            readings = self.process_meter_data()
            if readings:
                self.display_readings(readings)
                return [
                    {"key": "WirkenergieP", "value": readings.get("absolute_energy_in")},
                    {"key": "WirkenergieN", "value": readings.get("absolute_energy_out")},
                    {"key": "absolute_energy_in", "value": readings.get("absolute_energy_in")},
                    {"key": "absolute_energy_out", "value": readings.get("absolute_energy_out")}
                ]
        except KeyboardInterrupt:
            self.port.close()
    
    def display_readings(self, data):
        if not data.get('timestamp'):
            print("\n*** Cannot find OBIS codes - Key error? ***\n")
            return

        obis = {
            'timestamp': data['timestamp'],
            'meter_serial_number': data['meter_serial_number'],
            'logical_device_name': data['logical_device_name'],
            'l1_voltage': data['l1_voltage'],
            'l2_voltage': data['l2_voltage'],
            'l3_voltage': data['l3_voltage'],
            'l1_current': data['l1_current'],
            'l2_current': data['l2_current'],
            'l3_current': data['l3_current'],
            'power_in': data['power_in'],
            'power_out': data['power_out'],
            'absolute_energy_in': data['absolute_energy_in'],
            'absolute_energy_out': data['absolute_energy_out'],
            'reactive_energy_in': data['reactive_energy_in'],
            'reactive_energy_out': data['reactive_energy_out']
        }
        
        '''print(f"0.0.1.0.0.255\tDate Time:\t\t\t {data['timestamp']}")
        print(f"0.0.96.1.0.255\tMeter Number:\t\t\t {data['meter_id']}")
        print(f"0.0.42.0.0.255\tCOSEM Device Name:\t\t {data['device_name']}")
        print(f"1.0.32.7.0.255\tVoltage L1 (V):\t\t\t {data['voltage_l1']}")
        print(f"1.0.52.7.0.255\tVoltage L2 (V):\t\t\t {data['voltage_l2']}")
        print(f"1.0.72.7.0.255\tVoltage L3 (V):\t\t\t {data['voltage_l3']}")
        print(f"1.0.31.7.0.255\tCurrent L1 (A):\t\t\t {data['current_l1']}")
        print(f"1.0.51.7.0.255\tCurrent L2 (A):\t\t\t {data['current_l2']}")
        print(f"1.0.71.7.0.255\tCurrent L3 (A):\t\t\t {data['current_l3']}")
        print(f"1.0.1.7.0.255\tActive Power Import [kW]:\t {data['power_in']}")
        print(f"1.0.2.7.0.255\tActive Power Export [kW]:\t {data['power_out']}")
        print(f"1.0.1.8.0.255\tActive Energy Import [kWh]:\t {data['energy_in']}")
        print(f"1.0.2.8.0.255\tActive Energy Export [kWh]:\t {data['energy_out']}")
        print(f"1.0.3.8.0.255\tReactive Energy Import [kW]:\t {data['reactive_in']}")
        print(f"1.0.4.8.0.255\tReactive Energy Export [kW]:\t {data['reactive_out']}")
    '''

if __name__ == '__main__':
    meter = TinetzKaifa309MReader()
    meter.read_frame()