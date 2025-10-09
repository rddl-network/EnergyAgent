#!/usr/bin/env python3
"""
Test updated Python frame parsing to match C code improvements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'energy_agent', 'smart_meter_reader'))

from dhlc_blocks import SmartMeterPayloadExtractor

# Test data from frameset_test.py (same data used to test C code)
test_hex_data = """7e3b3d02a4b4f1de003b284d4b5a5775034f029520a31b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520a71b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520ab1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520af1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520b31b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520b71b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520bb1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520bf1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520c31b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520c71b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520cb1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520cf1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520d31b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520d71b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520db1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520df1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520e31b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520e71b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520eb1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520ef1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520f31b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520f71b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520fb1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f029520ff1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295201302ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f0295201702ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f029520171b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295201b1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295201f1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295202302ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f0295202702ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f029520271b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295202b1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295202f1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295203302ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f0295203702ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f029520371b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295203b1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295203f1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295204302ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f0295204702ebca7e7e3b3d02a4b4f1de003b284d4b5a5775034f029520471b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295204b1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295204f1b71fca07e7e3b3d02a4b4f1de003b284d4b5a5775034f0295205302ebca7e"""

def test_python_frame_parsing():
    """Test the updated Python frame parsing"""
    print("🧪 Testing Updated Python Frame Parsing")
    print("=" * 60)
    
    # Clean the hex data
    hex_data = test_hex_data.replace('\n', '').replace(' ', '')
    print(f"📊 Test data length: {len(hex_data)} hex characters ({len(hex_data)//2} bytes)")
    
    # Create payload extractor
    extractor = SmartMeterPayloadExtractor()
    
    # Disable decryption for this test to focus on frame parsing
    extractor.enable_dlms_decryption(False)
    
    # Process the payload
    results = extractor.process_hex_payload(hex_data)
    
    # Analyze results
    print(f"\n📈 Frame Parsing Results:")
    print(f"   Total frames processed: {extractor.frame_count}")
    print(f"   Data blocks extracted: {len(results)}")
    
    # Count frame types based on MSB patterns
    encrypted_count = 0
    standard_count = 0
    other_count = 0
    
    for block in results:
        # Check if this block was identified as encrypted (MSB=0x95 pattern)
        raw_data = bytes.fromhex(block['raw_data'])
        if len(raw_data) > 0:
            # For these test frames, the MSB byte should be at position 0 after payload extraction
            msb_byte = raw_data[0] if raw_data else 0
            if msb_byte == 0x95:
                encrypted_count += 1
            elif msb_byte == 0x03:
                standard_count += 1
            else:
                other_count += 1
    
    print(f"\n🔍 Frame Type Analysis:")
    print(f"   Encrypted frames (MSB=0x95): {encrypted_count}")
    print(f"   Standard frames (MSB=0x03): {standard_count}")
    print(f"   Other frame types: {other_count}")
    
    # Expected results from C code test
    expected_total = 42
    expected_encrypted = 34
    
    print(f"\n✅ Validation against C code results:")
    print(f"   Expected total frames: {expected_total}")
    print(f"   Actual total frames: {extractor.frame_count}")
    print(f"   Expected encrypted: {expected_encrypted}")
    print(f"   Actual encrypted: {encrypted_count}")
    
    # Check if results match
    if extractor.frame_count == expected_total:
        print(f"   ✅ Total frame count matches C code!")
    else:
        print(f"   ❌ Total frame count mismatch")
    
    if encrypted_count == expected_encrypted:
        print(f"   ✅ Encrypted frame count matches C code!")
    else:
        print(f"   ❌ Encrypted frame count mismatch")
    
    # Show sample frame details
    if results:
        print(f"\n📋 Sample Frame Details:")
        sample = results[0]
        print(f"   Block ID: {sample['block_id']}")
        print(f"   Type: {sample['type']}")
        print(f"   Size: {sample['total_size']} bytes")
        print(f"   Raw data: {sample['raw_data'][:50]}...")
    
    return extractor.frame_count == expected_total and encrypted_count == expected_encrypted

if __name__ == "__main__":
    success = test_python_frame_parsing()
    
    if success:
        print(f"\n🎉 Python frame parsing successfully matches C code behavior!")
        exit(0)
    else:
        print(f"\n❌ Python frame parsing does not match C code behavior")
        exit(1)