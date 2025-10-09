#!/usr/bin/env python3
"""
Fixed Frame Parsing for HDLC
This correctly extracts frames from concatenated data by respecting 7E boundaries
"""

def extract_frames_correctly(hex_data):
    """
    Correctly extract HDLC frames from concatenated hex data
    
    Args:
        hex_data: String of concatenated hex data containing multiple 7E-delimited frames
    
    Returns:
        List of dictionaries with frame details
    """
    # Convert hex string to bytes
    if isinstance(hex_data, str):
        data = bytes.fromhex(hex_data)
    else:
        data = hex_data
    
    frames = []
    i = 0
    frame_count = 0
    
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
                # Extract complete frame (including both 7E markers)
                frame_data = data[frame_start:frame_end + 1]
                
                # Analyze frame structure
                frame_info = analyze_frame_structure(frame_data, frame_count)
                frames.append(frame_info)
                
                frame_count += 1
                i = frame_end + 1  # Move past this frame
            else:
                # No closing 7E found
                print(f"⚠️  No closing 7E found for frame starting at position {i}")
                break
        else:
            i += 1
    
    return frames

def analyze_frame_structure(frame_data, frame_index):
    """
    Analyze the structure of a single HDLC frame
    """
    frame_hex = frame_data.hex().upper()
    
    # Basic frame analysis
    info = {
        'frame_index': frame_index,
        'length_bytes': len(frame_data),
        'frame_hex': frame_hex,
        'has_start_flag': frame_data[0] == 0x7E if len(frame_data) > 0 else False,
        'has_end_flag': frame_data[-1] == 0x7E if len(frame_data) > 0 else False,
    }
    
    # Extract content between 7E flags
    if len(frame_data) > 2:
        content = frame_data[1:-1]  # Remove start and end 7E
        info['content_hex'] = content.hex().upper()
        info['content_length'] = len(content)
        
        # Check for MSB pattern - should be at positions 16-17 (0x10-0x11)
        if len(content) >= 18:
            msb_bytes = content[16:18]
            info['msb_bytes'] = msb_bytes.hex().upper()
            
            # Interpret MSB flags
            if msb_bytes == bytes.fromhex('03B8'):
                info['msb_flag'] = 'continuation'
            elif msb_bytes == bytes.fromhex('0338'):
                info['msb_flag'] = 'end'
            else:
                info['msb_flag'] = f'unknown_{msb_bytes.hex()}'
                
        # Check for header pattern (should be consistent)
        if len(content) >= 16:
            header = content[0:16]
            info['header_hex'] = header.hex().upper()
            
            # Expected pattern: 3B3D02A4B4F1DE003B284D4B5A5775034F02
            expected_start = "3B3D02A4B4F1DE003B284D4B5A5775034F02"
            if header.hex().upper() == expected_start:
                info['header_valid'] = True
            else:
                info['header_valid'] = False
                info['header_diff'] = f"Expected: {expected_start}, Got: {header.hex().upper()}"
    
    return info

def test_with_your_data():
    """
    Test the corrected parsing with your problematic data
    """
    # Your concatenated data
    concat_data = "7e3b3d02a4b4f1de003b284d4b5a5775034f0203b8a61d3ae83b89b601aa264fdaae6a7d7ecfd7a2c3aa2579bd6a5961b8667e29dc3682d86d6bcb553f8879295951d48b24d407b9e9c6d92b5f16ebf97e3b3d02a4b4f1de003b284d4b5a5775034f0203383b75995925057f8591f9d767cd1c861553e954e6b7ed0d4839195e49551453f0acbb187e5a4df0e23f0c04034d592dc48d94c731ed6c75d9239fcbff7e3b3d02a4b4f1de003b284d4b5a5775034f0203b8e3326d1ec83b083b36e16cd49363d8cc0c2e1a45f60b74229dbbaa5b0dde82330e8423a82f8c282b6d1aece66579428c3738631cf3540b2dd2e5ff7e3b3d02a4b4f1de003b284d4b5a5775034f02033883f039abac6b4d57751dbe28d2f9984225136f3324176c3d1333d1ca90d38604fbd22ded3866516d456be10069b0f8414a0dc074e28d9d551804e9ff7e3b3d02a4b4f1de003b284d4b5a5775034f0203b893b7611ec56d05ae69e8aa5a2d020d234a940f715a8f753461d4a2a428ab8e3fbe26cf739f25b3cd0e09164ca40b696e2eae7a5d6b18db123a51cfff7e3b3d02a4b4f1de003b284d4b5a5775034f0203385ab27147f512479b3a885289ab150c0aedcf0a026bc2bac28d3664f91a4926a1b5e671acb6c5f63e0ea9e958d299eee6ad4d1299d70ddb69467e7e3b3d02a4b4f1de003b284d4b5a5775034f0203b89afbdea33a69fab9d2ba5fc88e35c9e52c41722116fcdae22dd30ef9ad8b71d73a5c5069b17377936cd5f46919c4837aa49ff52a3b45b65c9f4ad6f3ff7e3b3d02a4b4f1de003b284d4b5a5775034f0203381a665526474e5613a33152844b8d24cd2a021ccc124f6cf620da043e67e65cc361b19aa92f4eb21dddf79ad7c24896d21575a559e8b56d0ac33439657e"
    
    print("🔧 **CORRECTED FRAME EXTRACTION**")
    print("=" * 50)
    
    frames = extract_frames_correctly(concat_data)
    
    print(f"✅ **Extracted {len(frames)} frames correctly**\n")
    
    for frame in frames:
        print(f"📦 **Frame {frame['frame_index']}:**")
        print(f"   Length: {frame['length_bytes']} bytes")
        print(f"   Start Flag: {'✅' if frame['has_start_flag'] else '❌'}")
        print(f"   End Flag: {'✅' if frame['has_end_flag'] else '❌'}")
        print(f"   Header Valid: {'✅' if frame.get('header_valid', False) else '❌'}")
        
        if 'msb_flag' in frame:
            flag_emoji = "🔄" if frame['msb_flag'] == 'continuation' else "🏁" if frame['msb_flag'] == 'end' else "❓"
            print(f"   MSB Flag: {flag_emoji} {frame['msb_flag']} ({frame.get('msb_bytes', 'N/A')})")
        
        if not frame.get('header_valid', True):
            print(f"   ⚠️  Header Issue: {frame.get('header_diff', 'Unknown')}")
        
        print()
    
    return frames

if __name__ == "__main__":
    test_with_your_data()