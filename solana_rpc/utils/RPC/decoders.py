import base64
import base58
import zstandard as zstd  # Make sure you install this library: pip install zstandard

def decode_on_type(data, encoding):
    if encoding == "base64":
        return base64.b64decode(data)
    elif encoding == "base58":
        return base58.b58decode(data)
    elif encoding == "base64+zstd":
        # First decode from base64
        compressed_data = base64.b64decode(data)
        # Then decompress using Zstandard
        decompressor = zstd.ZstdDecompressor()
        return decompressor.decompress(compressed_data)
    elif encoding == "jsonParsed":
        # If using json parsed and was successful, should already be dict or list
        if isinstance(data, dict) or isinstance(data, list):
            return data
        else:
            # If jsonParsed fails, it's actually base64-encoded, so decode it as base64
            return base64.b64decode(data)
    else:
        raise ValueError(f"Unsupported encoding type: {encoding}")
