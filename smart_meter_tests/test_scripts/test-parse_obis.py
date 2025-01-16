import xml.etree.ElementTree as ET
from datetime import datetime
import binascii

class DLMSNotificationParser:
    def __init__(self):
        self.obis_codes = {
            "0008190900FF": "Configuration Parameter",
            "0000600100FF": "Clock Sync Parameter",
            "0000010000FF": "Device Identification"
        }
        
        self.value_types = {
            "01": "Normal Reading",
            "02": "Status Change"
        }

    def parse_datetime(self, hex_datetime):
        """Parse DLMS datetime format from hex string"""
        try:
            # Extract components from hex string
            year = int(hex_datetime[0:4], 16)
            month = int(hex_datetime[4:6], 16)
            day = int(hex_datetime[6:8], 16)
            hour = int(hex_datetime[8:10], 16)
            minute = int(hex_datetime[10:12], 16)
            second = int(hex_datetime[12:14], 16)
            
            return datetime(year, month, day, hour, minute, second)
        except ValueError as e:
            return f"Error parsing datetime: {e}"

    def parse_notification(self, xml_string):
        """Parse complete XML notification"""
        try:
            root = ET.fromstring(xml_string)
            
            # Parse basic notification info
            result = {
                "invoke_id": root.find("LongInvokeIdAndPriority").get("Value"),
                "datetime": self.parse_datetime(root.find("DateTime").get("Value")),
                "structures": []
            }
            
            # Parse data structures
            data_value = root.find("NotificationBody/DataValue")
            if data_value is not None:
                for structure in data_value.findall(".//Structure"):
                    struct_data = self.parse_structure(structure)
                    if struct_data:
                        result["structures"].append(struct_data)
            
            return result
        except Exception as e:
            return f"Error parsing notification: {e}"

    def parse_structure(self, structure):
        """Parse individual structure elements"""
        try:
            elements = structure.findall("*")
            if len(elements) < 4:
                return None
                
            obis = elements[1].get("Value") if len(elements) > 1 else None
            
            return {
                "id": elements[0].get("Value"),
                "obis_code": obis,
                "obis_meaning": self.obis_codes.get(obis, "Unknown Parameter"),
                "value_type": elements[2].get("Value") if len(elements) > 2 else None,
                "value_meaning": self.value_types.get(elements[2].get("Value"), "Unknown Type"),
                "status": elements[3].get("Value") if len(elements) > 3 else None
            }
        except Exception as e:
            return f"Error parsing structure: {e}"

    def print_notification(self, parsed_data):
        """Print parsed notification in readable format"""
        print("\nDLMS/COSEM Notification Report")
        print("=" * 40)
        print(f"Invoke ID: {parsed_data['invoke_id']}")
        print(f"Timestamp: {parsed_data['datetime']}")
        print("\nStructures:")
        print("-" * 40)
        
        for idx, structure in enumerate(parsed_data['structures'], 1):
            print(f"\nStructure {idx}:")
            print(f"  ID: {structure['id']}")
            print(f"  OBIS Code: {structure['obis_code']}")
            print(f"  Parameter: {structure['obis_meaning']}")
            print(f"  Value Type: {structure['value_type']} ({structure['value_meaning']})")
            print(f"  Status: {structure['status']}")

# Example usage
def parse_example():
    parser = DLMSNotificationParser()
    
    # Example XML string - replace with actual XML
    xml_example = """
    <DataNotification>
        <LongInvokeIdAndPriority Value="00B1CA8F" />
        <DateTime Value="07E70A0C040C3100FF800000" />
        <NotificationBody>
            <DataValue>
                <Structure Qty="12">
                    <Array Qty="12">
                        <Structure Qty="04">
                            <UInt16 Value="0028" />
                            <OctetString Value="0008190900FF" />
                            <Int8 Value="02" />
                            <UInt16 Value="0000" />
                        </Structure>
                    </Array>
                </Structure>
            </DataValue>
        </NotificationBody>
    </DataNotification>
    """
    
    result = parser.parse_notification(xml_example)
    parser.print_notification(result)

if __name__ == "__main__":
    parse_example()