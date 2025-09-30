# 光柵旋轉預測模型訓練

這個程式使用 PyTorch Ignite 框架訓練 `GratingRotationPredictorWithFftResnet18` 模型來預測光柵的旋轉角度。

## 功能特點

- **雙分支架構**：結合 RGB 特徵和 FFT 特徵
- **自動模型保存**：當驗證損失降低時自動保存最佳模型
- **TensorBoard 日誌**：記錄訓練和驗證損失
- **早停機制**：防止過擬合
- **完整的日誌記錄**：檔案和控制台輸出

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 使用方法

1. **準備資料**：
   - 將圖片放在 `rotated-grating-images-topview/images/` 目錄
   - 確保 Excel 檔案 `rotated-grating-images-topview/images-and-grating-rotation.ods` 存在

2. **基本執行**：
   ```bash
   python train_grating_rotation_prediction_model.py
   ```

3. **自定義參數執行**：
   ```bash
   python train_grating_rotation_prediction_model.py \
     --batch_size 32 \
     --learning_rate 0.001 \
     --num_epochs 200 \
     --log_to_file \
     --tensorboard_dir custom_tb_logs
   ```

4. **從檢查點恢復訓練**：
   ```bash
   python train_grating_rotation_prediction_model.py \
     --resume_from models/checkpoint_epoch_50.pth
   ```

5. **查看結果**：
   - 模型保存在 `models/` 目錄
   - 日誌保存在 `logs/` 目錄
   - TensorBoard 日誌：`tensorboard --logdir logs/tensorboard`

## 命令列參數

### 資料參數
- `--root_dir`: 圖片根目錄 (預設: "rotated-grating-images-topview/images")
- `--excel_file_path`: Excel 檔案路徑 (預設: "rotated-grating-images-topview/images-and-grating-rotation.ods")
- `--image_extension`: 圖片副檔名 (預設: "png")

### 訓練參數
- `--batch_size`: 批次大小 (預設: 16)
- `--learning_rate`: 學習率 (預設: 1e-4)
- `--num_epochs`: 訓練輪數 (預設: 100)
- `--patience`: 早停耐心值 (預設: 10)
- `--train_split`: 訓練集比例 (預設: 0.8)
- `--num_workers`: 資料載入工作進程數 (預設: 4)

### 模型參數
- `--device`: 運算設備 (預設: "auto", 選項: "auto", "cpu", "cuda")

### 日誌和輸出參數
- `--log_dir`: 日誌目錄 (預設: "logs")
- `--model_save_dir`: 模型保存目錄 (預設: "models")
- `--log_level`: 日誌級別 (預設: "INFO", 選項: "DEBUG", "INFO", "WARNING", "ERROR")
- `--log_to_file`: 啟用檔案日誌
- `--no_console_log`: 停用控制台日誌
- `--tensorboard_dir`: TensorBoard 日誌目錄 (預設: {log_dir}/tensorboard)

### 其他參數
- `--resume_from`: 從檢查點恢復訓練
- `--val_frequency`: 驗證頻率 (每 N 個 epoch) (預設: 1)
- `--save_frequency`: 保存頻率 (每 N 個 epoch) (預設: 10)

## 使用範例

### 快速開始
```bash
python train_grating_rotation_prediction_model.py
```

### 高精度訓練
```bash
python train_grating_rotation_prediction_model.py \
  --batch_size 8 \
  --learning_rate 5e-5 \
  --num_epochs 300 \
  --patience 20
```

### 調試模式
```bash
python train_grating_rotation_prediction_model.py \
  --log_level DEBUG \
  --log_to_file \
  --num_epochs 5
```

### 從檢查點恢復
```bash
python train_grating_rotation_prediction_model.py \
  --resume_from models/checkpoint_epoch_100.pth \
  --num_epochs 200
```

## 模型架構

- **RGB 分支**：ResNet18 提取 RGB 特徵
- **FFT 分支**：對圖像進行 FFT 轉換後用 ResNet18 提取特徵
- **融合層**：將兩個分支的特徵連接後通過全連接層預測旋轉角度

## 輸出檔案

- `models/best_model.pth`: 最佳模型權重
- `models/final_model.pth`: 最終模型權重
- `models/model_epoch_X.pth`: 每 10 個 epoch 的模型快照
- `logs/training.log`: 訓練日誌
- `logs/tensorboard/`: TensorBoard 日誌目錄
