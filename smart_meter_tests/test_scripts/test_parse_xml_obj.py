import xml.etree.ElementTree as ET
from datetime import datetime


def parse_datetime(hex_datetime):
    """Parse the hexadecimal datetime string into a readable format."""
    year = int(hex_datetime[0:4], 16)
    month = int(hex_datetime[4:6], 16)
    day = int(hex_datetime[6:8], 16)
    hour = int(hex_datetime[8:10], 16)
    minute = int(hex_datetime[10:12], 16)
    second = int(hex_datetime[12:14], 16)

    formatted_date = datetime(year, month, day, hour, minute, second)

    return {
        "raw": hex_datetime,
        "formatted": formatted_date.strftime("%Y-%m-%d %H:%M:%S"),
        "components": {"year": year, "month": month, "day": day, "hour": hour, "minute": minute, "second": second},
    }


def parse_data_notification(xml_string):
    """Parse the XML data notification string into a Python dictionary."""
    # Parse XML string
    root = ET.fromstring(xml_string)

    # Extract main components
    result = {
        "invokeId": root.find("LongInvokeIdAndPriority").get("Value"),
        "datetime": parse_datetime(root.find("DateTime").get("Value")),
        "structures": [],
    }

    # Find all Structure elements within Array
    array = root.find(".//Array")
    if array is not None:
        for structure in array.findall("Structure"):
            structure_data = {
                "uint16": structure.find("UInt16").get("Value") if structure.find("UInt16") is not None else None,
                "octetString": (
                    structure.find("OctetString").get("Value") if structure.find("OctetString") is not None else None
                ),
                "int8": structure.find("Int8").get("Value") if structure.find("Int8") is not None else None,
                "uint16_2": (
                    structure.findall("UInt16")[1].get("Value") if len(structure.findall("UInt16")) > 1 else None
                ),
            }
            result["structures"].append(structure_data)

    return result


# Example usage
xml_data = """<DataNotification>
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
          <Structure Qty="04">
            <UInt16 Value="0028" />
            <OctetString Value="0008190900FF" />
            <Int8 Value="01" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0001" />
            <OctetString Value="0000600100FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0008" />
            <OctetString Value="0000010000FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
          </Structure>
        </Array>
      </Structure>
    </DataValue>
  </NotificationBody>
</DataNotification>"""

if __name__ == "__main__":
    try:
        parsed_data = parse_data_notification(xml_data)
        # Print the result in a nicely formatted way
        import json

        print(json.dumps(parsed_data, indent=2))
    except Exception as e:
        print(f"Error parsing XML: {e}")
