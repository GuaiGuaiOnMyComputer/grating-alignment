import cv2
import json
import base64
import numpy as np
import requests
from time import sleep
from pathlib import Path
from typing import Tuple

def _encode_img_as_b64_string(img_path: Path) -> Tuple[str, int, int]:
    test_image_path: Path = Path("test") / Path("lenna-demo-img.jpg")
    test_img: np.ndarray = cv2.imread(str(test_image_path))

    test_img_as_bytes:bytes = test_img.tobytes()
    test_img_as_b64_str:str = base64.b64encode(test_img_as_bytes).decode('utf-8')

    return test_img_as_b64_str, test_img.shape[1], test_img.shape[0]

def main():

    img_as_b64_str, width, height = _encode_img_as_b64_string(Path("lenna-demo-img.jpg"))
    status_code = 4 # 完成光柵對齊
    latest_frame_as_dict = {"width": width, "height": height, "data": img_as_b64_str}
    displacement = float('inf')
    message = "Alignment Complete"

    payload_json:str = json.dumps({
        "status_code": status_code,
        "latest_frame": latest_frame_as_dict,
        "displacement": displacement,
        "message": message
    }, allow_nan = True, indent = 4)

    try:
        url = "http://localhost:6666/upload"
        requests.post(url, json = payload_json)
    except Exception:
        print("Cannot send payload to end point due to connection error.")

    print("Payload sent to url:")
    print(payload_json)

    with open("payload.json", "w") as f:
        f.write(payload_json)
        print("\n")
        print("Payload is also written to file payload.json")

    print("Decoding the json payload in 2 seconds.")
    sleep(2)

    del img_as_b64_str

    payload_json_decode:dict = json.loads(payload_json)
    img_width = payload_json_decode["latest_frame"]["width"]
    img_height = payload_json_decode["latest_frame"]["height"]

    img_as_b64_str:str = base64.b64decode(payload_json_decode["latest_frame"]["data"])
    img_as_array = np.frombuffer(img_as_b64_str, dtype = np.uint8).reshape((img_height, img_width, 3))
    cv2.imshow("Decoded image from base64 string", img_as_array)
    cv2.waitKey(0)


    


if __name__ == "__main__":
    main()
