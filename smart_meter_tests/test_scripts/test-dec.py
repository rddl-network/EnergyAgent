from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from Crypto.Util.Padding import pad, unpad
import binascii

class LandisGyrDecryptor:
    def __init__(self, encryption_key: str, auth_key: str):
        self.encryption_key = bytes.fromhex(encryption_key)
        self.auth_key = bytes.fromhex(auth_key)
        self.block_size = AES.block_size  # 16 bytes for AES
    
    def pad_data(self, data):
        """Pad data to match AES block size"""
        return pad(data, self.block_size)
    
    def decrypt_frame(self, frame_hex: str):
        try:
            # Convert hex string to bytes
            frame_data = bytes.fromhex(frame_hex)
            
            # Extract frame components
            start_byte = frame_data[0]
            length = frame_data[1]
            control = frame_data[2]
            address = frame_data[3]
            
            # Extract encrypted payload
            encrypted_data = frame_data[4:-1]
            
            # Ensure data is properly padded
            if len(encrypted_data) % self.block_size != 0:
                padded_data = self.pad_data(encrypted_data)
            else:
                padded_data = encrypted_data
                
            print("\nAnalyzing Frame Structure:")
            print(f"Original data length: {len(encrypted_data)} bytes")
            print(f"Padded data length: {len(padded_data)} bytes")
            
            # Try different decryption approaches
            results = {}
            
            # Approach 1: ECB mode
            try:
                cipher_ecb = AES.new(self.encryption_key, AES.MODE_ECB)
                decrypted_ecb = cipher_ecb.decrypt(padded_data)
                results['ECB'] = {
                    'hex': decrypted_ecb.hex(),
                    'ascii': ''.join(chr(b) if 32 <= b <= 126 else '.' for b in decrypted_ecb)
                }
            except Exception as e:
                results['ECB'] = {'error': str(e)}
            
            # Approach 2: CBC mode with zero IV
            try:
                cipher_cbc = AES.new(self.encryption_key, AES.MODE_CBC, iv=b'\x00' * self.block_size)
                decrypted_cbc = cipher_cbc.decrypt(padded_data)
                results['CBC_ZERO_IV'] = {
                    'hex': decrypted_cbc.hex(),
                    'ascii': ''.join(chr(b) if 32 <= b <= 126 else '.' for b in decrypted_cbc)
                }
            except Exception as e:
                results['CBC_ZERO_IV'] = {'error': str(e)}
            
            # Approach 3: CBC mode with first block as IV
            try:
                if len(padded_data) >= self.block_size * 2:  # Need at least 2 blocks
                    iv = padded_data[:self.block_size]
                    cipher_cbc_iv = AES.new(self.encryption_key, AES.MODE_CBC, iv=iv)
                    decrypted_cbc_iv = cipher_cbc_iv.decrypt(padded_data[self.block_size:])
                    results['CBC_BLOCK_IV'] = {
                        'hex': decrypted_cbc_iv.hex(),
                        'ascii': ''.join(chr(b) if 32 <= b <= 126 else '.' for b in decrypted_cbc_iv)
                    }
            except Exception as e:
                results['CBC_BLOCK_IV'] = {'error': str(e)}
            
            # Try authentication
            try:
                cmac = CMAC.new(self.auth_key, ciphermod=AES)
                cmac.update(padded_data[:-self.block_size])
                calculated_tag = cmac.digest()
                received_tag = padded_data[-self.block_size:]
                
                auth_result = {
                    'received_tag': received_tag.hex(),
                    'calculated_tag': calculated_tag.hex(),
                    'is_valid': received_tag == calculated_tag
                }
            except Exception as e:
                auth_result = {'error': str(e)}
            
            # Print results
            print("\nDecryption Results:")
            for mode, result in results.items():
                print(f"\n{mode} Mode:")
                for key, value in result.items():
                    print(f"{key}: {value}")
            
            return {
                'frame_info': {
                    'start_byte': f'0x{start_byte:02X}',
                    'length': length,
                    'control': f'0x{control:02X}',
                    'address': f'0x{address:02X}'
                },
                'decryption_results': results,
                'authentication': auth_result
            }
            
        except Exception as e:
            print(f"\nError during decryption: {str(e)}")
            return {'error': str(e)}

# Test the decryption
frame = "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e87ea30fed7047d500c157a153258f4101eb0a5b892f58f62805ce0873f696990b95df9c45f40e3845d5e279cc33073504285e5d98a1c24a3efdf066cf1f1420f5da462b6410ebbd7896daad93a9d87e"
encryption_key = "4475D2230289243A4AE7732E2396C572"
auth_key = "8FEADE1D7057D94D816A41E09D17CB58"

decryptor = LandisGyrDecryptor(encryption_key, auth_key)
result = decryptor.decrypt_frame(frame)

print("\nFinal Frame Info:")
print("-" * 50)
for key, value in result['frame_info'].items():
    print(f"{key}: {value}")