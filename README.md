# 加斌光柵自動對位計畫

## 從光柵照片預測旋轉量

### 拍攝光柵圖片訓練集

拍攝光柵照片的相機為Basler acA4024-29UC，鏡頭使用20MP f 12mm 2.8mm，相機距離光柵板平面11cm。訓練照片都是灰階單通道的png影像，儲存於[grating_alignment](grating_alignment/rotated-grating-images-topview.tar)。此壓縮檔版本用gitlfs追蹤，並上傳至Github。請用下列指令下載git lfs檔案。

```bash
# 下載git lfs檔案
git lfs install
git lfs pull
```

光柵旋轉量在拍攝照片時使用直尺和arctan函數求得，記錄在
[grating_alignment](grating_alignment/rotated-grating-images-topview.tar)
裡的兩分試算表。

## 步進馬達接線與控制

### 接線

Jetson Orin Nano與Arduino之間使用USB供電與通訊，其他元件的接線方式如下:

|Arduino Uno|TMC2209|步進馬達57BYGH56|24V電源供應器|功能|
|-----------|-------|---------------|------------|----|
|7          |EN     |               |            |允許馬達線圈通電|
|10         |TX     |               |            |Software Serial RX|
|11         |RX     |               |            |Software Serial TX|
|GND        |GND    |               |            |共同接地|
|5V         |VIO    |               |            |邏輯電壓|
|           |A2     |綠A-           |            |馬達A相負極|
|           |A1     |紅A+           |            |馬達A相正極|
|           |B1     |藍B+           |            |馬達B相正極|
|           |B2     |黃B-           |            |馬達B相負極|
|           |VM     |               |V+          |馬達驅動電源|
|           |GND    |               |V-          |與arduino和驅動板共同接地|
