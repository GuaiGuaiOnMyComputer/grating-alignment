from typing import NamedTuple
import json
import numpy as np

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