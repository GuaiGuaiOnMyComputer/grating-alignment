from typing import NamedTuple
import json
import numpy as np
import base64

class SerializedImage(NamedTuple):

    data: str
    width: int
    height: int

def serialize_numpy_to_json(array: np.ndarray) -> str:
    """
    將 numpy 陣列序列化為 JSON 字串
    
    Args:
        array: 要序列化的 numpy 陣列
        
    Returns:
        JSON 字串格式的序列化陣列
    """
    # 將 numpy 陣列轉換為 Python 列表
    array_list = array.tolist()
    
    # 序列化為 JSON 字串
    json_string = json.dumps(array_list)
    
    return json_string

def deserialize_json_to_numpy(json_string: str, dtype: np.dtype = None) -> np.ndarray:
    """
    將 JSON 字串反序列化為 numpy 陣列
    
    Args:
        json_string: JSON 格式的字串
        dtype: 可選的 numpy 資料型別
        
    Returns:
        反序列化後的 numpy 陣列
    """
    # 從 JSON 字串解析為 Python 列表
    array_list = json.loads(json_string)
    
    # 轉換為 numpy 陣列
    array = np.array(array_list, dtype=dtype)
    
    return array

def serialize_numpy_to_base64(array: np.ndarray) -> str:
    """
    將 numpy 陣列序列化為 base64 字串
    
    Args:
        array: 要序列化的 numpy 陣列
        
    Returns:
        base64 編碼的字串
    """
    # 將 numpy 陣列轉換為位元組
    array_bytes = array.tobytes()
    
    # 編碼為 base64 字串
    base64_string = base64.b64encode(array_bytes).decode('utf-8')
    
    return base64_string

def deserialize_base64_to_numpy(base64_string: str, dtype: np.dtype, shape: tuple) -> np.ndarray:
    """
    將 base64 字串反序列化為 numpy 陣列
    
    Args:
        base64_string: base64 編碼的字串
        dtype: numpy 資料型別
        shape: 陣列的形狀
        
    Returns:
        反序列化後的 numpy 陣列
    """
    # 解碼 base64 字串為位元組
    array_bytes = base64.b64decode(base64_string)
    
    # 從位元組重建 numpy 陣列
    array = np.frombuffer(array_bytes, dtype=dtype).reshape(shape)
    
    return array

def serialize_numpy_to_base64_with_metadata(array: np.ndarray) -> dict:
    """
    將 numpy 陣列序列化為 base64 字串並包含元數據
    
    Args:
        array: 要序列化的 numpy 陣列
        
    Returns:
        包含 base64 數據和元數據的字典
    """
    base64_data = serialize_numpy_to_base64(array)
    
    metadata = {
        'data': base64_data,
        'dtype': str(array.dtype),
        'shape': array.shape,
        'size': array.size
    }
    
    return metadata

def deserialize_base64_with_metadata(metadata: dict) -> np.ndarray:
    """
    從包含元數據的字典反序列化 numpy 陣列
    
    Args:
        metadata: 包含 base64 數據和元數據的字典
        
    Returns:
        反序列化後的 numpy 陣列
    """
    base64_data = metadata['data']
    dtype = np.dtype(metadata['dtype'])
    shape = tuple(metadata['shape'])
    
    return deserialize_base64_to_numpy(base64_data, dtype, shape)