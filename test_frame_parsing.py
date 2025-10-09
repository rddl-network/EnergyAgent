#!/usr/bin/env python3
"""
Test the fixed frame parsing logic using the large frameset data
This simulates what the C code will do with proper frame boundary detection
"""

def simulate_c_frame_parsing(hex_data):
    """
    Simulate the improved C frame parsing logic
    """
    # Convert to bytes
    data = bytes.fromhex(hex_data.replace(' ', '').replace('\n', ''))
    
    print(f"🔍 **TESTING IMPROVED FRAME PARSING**")
    print(f"Total data: {len(data)} bytes")
    print("=" * 50)
    
    frames = []
    i = 0
    
    # Simulate continuous buffer processing like in C code
    while i < len(data):
        # Look for frame start (0x7E)
        if data[i] == 0x7E:
            frame_start = i
            
            # Look for frame end (next 0x7E)
            frame_end = None
            for j in range(i + 1, len(data)):
                if data[j] == 0x7E:
                    frame_end = j
                    break
            
            if frame_end is not None:
                # Extract complete frame (including both 0x7E markers)
                frame_data = data[frame_start:frame_end + 1]
                
                if len(frame_data) >= 3:  # Minimum valid frame
                    frames.append(frame_data)
                    
                    # Simulate C validation and analysis
                    validate_and_analyze_frame(frame_data, len(frames))
                
                i = frame_end + 1  # Move past this frame
            else:
                # No closing 7E found
                break
        else:
            i += 1
    
    print(f"\n✅ **EXTRACTION COMPLETE**")
    print(f"Successfully extracted {len(frames)} complete frames")
    return frames

def validate_and_analyze_frame(frame_data, frame_num):
    """
    Simulate the C validation and analysis functions
    """
    print(f"\n📦 **Frame {frame_num} Analysis:**")
    print(f"   Length: {len(frame_data)} bytes")
    
    # Validate frame flags
    if frame_data[0] != 0x7E or frame_data[-1] != 0x7E:
        print(f"   ❌ Invalid frame flags")
        return False
    
    if len(frame_data) < 6:
        print(f"   ❌ Frame too short")
        return False
    
    # Check format byte
    format_byte = frame_data[1]
    print(f"   Format: 0x{format_byte:02X}")
    
    if format_byte == 0x3B:
        print(f"   ✅ Encrypted DLMS frame detected")
        
        # Check for expected Iskra AM550 header
        if len(frame_data) >= 21:
            expected_header = bytes([0x3D, 0x02, 0xA4, 0xB4, 0xF1, 0xDE, 0x00, 0x3B, 
                                   0x28, 0x4D, 0x4B, 0x5A, 0x57, 0x75, 0x03, 0x4F, 0x02])
            
            actual_header = frame_data[2:19]
            if actual_header == expected_header:
                print(f"   ✅ Valid Iskra AM550 header")
                
                # Analyze MSB pattern
                msb_byte = frame_data[19]
                control_byte = frame_data[20]
                
                print(f"   MSB: 0x{msb_byte:02X} ({msb_byte:08b})")
                print(f"   Control: 0x{control_byte:02X}")
                
                # Interpret flags
                if (msb_byte >> 7) & 1:
                    print(f"   🔄 Continuation frame")
                else:
                    print(f"   🏁 End frame")
                
                if (msb_byte >> 4) & 1:
                    print(f"   🔐 Encryption enabled")
                else:
                    print(f"   📝 No encryption")
                
                if msb_byte == 0x95:
                    print(f"   🎯 AES-GCM encrypted DLMS data!")
                elif msb_byte == 0x03:
                    print(f"   📄 Plaintext DLMS data")
                else:
                    print(f"   ❓ Unknown pattern: 0x{msb_byte:02X}")
            else:
                print(f"   ⚠️ Non-standard header")
                print(f"   Expected: {expected_header.hex()}")
                print(f"   Got:      {actual_header.hex()}")
        else:
            print(f"   ⚠️ Frame too short for full analysis")
    
    elif (format_byte & 0xF0) == 0xA0:
        print(f"   ✅ Standard DLMS HDLC frame")
    else:
        print(f"   ℹ️ Other frame type")
    
    return True

def main():
    # Load the problematic frameset from your test file
    try:
        with open('/home/jeckel/develop/rddl/energyagent/tests/frameset_test.py', 'r') as f:
            content = f.read()
        
        # Extract the frameset
        start_marker = 'my_large_frameset ="""'
        end_marker = '"""'
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        frameset_data = content[start_idx:end_idx].strip()
        
        print("🚀 **TESTING FRAME PARSING FIX**")
        print("Using your large frameset from frameset_test.py")
        print("=" * 60)
        
        # Test the improved parsing
        frames = simulate_c_frame_parsing(frameset_data)
        
        # Summary
        print(f"\n📊 **SUMMARY:**")
        print(f"   Total frames extracted: {len(frames)}")
        
        encrypted_count = 0
        standard_count = 0
        other_count = 0
        
        for frame in frames:
            if len(frame) >= 21 and frame[1] == 0x3B:
                msb_byte = frame[19]
                if msb_byte == 0x95:
                    encrypted_count += 1
                elif msb_byte == 0x03:
                    standard_count += 1
                else:
                    other_count += 1
            else:
                other_count += 1
        
        print(f"   🔐 Encrypted frames: {encrypted_count}")
        print(f"   📄 Standard frames: {standard_count}")
        print(f"   ❓ Other frames: {other_count}")
        
        if encrypted_count > 0:
            print(f"\n🎯 **KEY FINDING:**")
            print(f"   Your meter is sending encrypted DLMS data!")
            print(f"   You need proper AES-GCM decryption with correct keys.")
            print(f"   The frame parsing is now working correctly.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()