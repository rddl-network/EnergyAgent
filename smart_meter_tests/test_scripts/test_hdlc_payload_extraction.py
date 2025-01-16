class HDLCFrameProcessor:
    def __init__(self):
        self.START_FLAG = 0x7E
        self.FORMAT_TYPE = 0xA0
        self.BASE_HEADER_LENGTH = 8  # Base length of fixed header (format type + control/address)
        self.SEG_CONTROL_LENGTH = 5  # Length of segmentation control field (e040000x00)
        
    def clean_hex_string(self, hex_string):
        """
        Clean hex string by removing whitespace and validating characters
        
        Args:
            hex_string: Raw hex string that might contain whitespace
            
        Returns:
            str: Cleaned hex string
        """
        # Remove whitespace and convert to lowercase
        cleaned = ''.join(hex_string.split()).lower()
        
        # Validate all characters are hex
        if not all(c in '0123456789abcdef' for c in cleaned):
            raise ValueError(f"Invalid hex characters in string")
            
        return cleaned

    def extract_payload(self, frames):
        """
        Extract and validate payloads from sequential HDLC frames
        
        Args:
            frames: List of hex strings containing HDLC frames
            
        Returns:
            dict: Contains combined payload and validation results
        """
        payloads = []
        validation = {"valid": True, "errors": []}
        
        last_seq = None
        
        for frame_idx, frame in enumerate(frames):
            try:
                # Clean and convert hex string to bytes
                cleaned_frame = self.clean_hex_string(frame)
                frame_bytes = bytes.fromhex(cleaned_frame)
                
                # Basic frame validation
                if len(frame_bytes) < 10:  # Minimum frame size
                    raise ValueError(f"Frame {frame_idx} too short")
                    
                if frame_bytes[0] != self.START_FLAG or frame_bytes[-1] != self.START_FLAG:
                    raise ValueError(f"Frame {frame_idx} missing HDLC flags")
                    
                if frame_bytes[1] != self.FORMAT_TYPE:
                    raise ValueError(f"Frame {frame_idx} invalid format type")
                
                # Extract length field
                declared_length = frame_bytes[2]
                actual_length = len(frame_bytes) - 2  # Subtract start/end flags and format/length bytes
                
                if declared_length != actual_length:
                    raise ValueError(f"Frame {frame_idx} length mismatch: declared={declared_length}, actual={actual_length}")
                
                if not last_seq:
                    # reading 3 addition bytes 
                    first_frame_data = frame_bytes[8:11]
                    seq_control = frame_bytes[12:17]  # e040000x00 portion
                    seq_num = seq_control[3]             
                else:
                    # added +1 for one additional control field that we found
                    # Extract sequence number (from the segmentation control field)
                    seq_control = frame_bytes[9:14]  # e040000x00 portion
                    seq_num = seq_control[3]             
  
                
                if last_seq is not None and seq_num != last_seq + 1:
                    raise ValueError(f"Frame {frame_idx} sequence mismatch")
                last_seq = seq_num
                
                # Determine if this frame has extra header bytes
                header_extra = 0
                if frame_idx == 0:  # First frame has extra e6e700 bytes
                    header_extra = 3
                
                # Extract payload (skip headers and control fields)
                payload_start = self.BASE_HEADER_LENGTH + header_extra + self.SEG_CONTROL_LENGTH
                payload_start = payload_start + 3
                payload_end = -2  # Remove end flag and checksum
                payload = frame_bytes[payload_start:payload_end]
                
                print(f"Frame {frame_idx} header analysis:")
                print(f"Base header: {frame_bytes[0:self.BASE_HEADER_LENGTH].hex()}")
                if header_extra:
                    print(f"Extra header: {frame_bytes[self.BASE_HEADER_LENGTH:self.BASE_HEADER_LENGTH+header_extra].hex()}")
                print(f"Seg control: {frame_bytes[self.BASE_HEADER_LENGTH+header_extra:self.BASE_HEADER_LENGTH+header_extra+self.SEG_CONTROL_LENGTH].hex()}")
                print(f"payload: {payload.hex()}")
                payloads.append(payload)
                
            except ValueError as e:
                validation["valid"] = False
                validation["errors"].append(str(e))
                return {"payload": None, "validation": validation}
        
        # Combine payloads
        combined_payload = b''.join(payloads)
        
        return {
            "payload": combined_payload.hex(),
            "validation": validation
        }
    
    def process_frames(self, frames):
        """
        Process a set of frames and print detailed analysis
        
        Args:
            frames: List of hex strings containing HDLC frames
        """
        print("Processing HDLC Frames:")
        print("-" * 50)
        
        for i, frame in enumerate(frames):
            frame_bytes = bytes.fromhex(frame)
            print(f"\nFrame {i+1}:")
            print(f"Length declared: {frame_bytes[2]}")
            print(f"Sequence control: {frame_bytes[8:13].hex()}")
            print(f"Payload size: {len(frame_bytes[13:-2])}")
        
        result = self.extract_payload(frames)
        print("\nValidation Result:")
        print(f"Valid: {result['validation']['valid']}")
        if not result['validation']['valid']:
            print("Errors:", result['validation']['errors'])
        
        if result['payload']:
            print(f"\nTotal payload size: {len(bytes.fromhex(result['payload']))} bytes")
            print(f"payload: {result['payload']}")

# Example usage
if __name__ == "__main__":
    # Example frames from the conversation
    test_frames = [
        "7ea08bceff0313eee1e6e700e0400001000077db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420ae57e",
        "7ea08bceff0313eee1e040000200007a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b80307197e",
        "7ea08bceff0313eee1e040000300007a68e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5257e",
        "7ea078ceff03138463e0c00004000067a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd0d7e"    
        ]
    
    processor = HDLCFrameProcessor()
    processor.process_frames(test_frames)
    

    