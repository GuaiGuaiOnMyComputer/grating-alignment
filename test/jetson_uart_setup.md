# Jetson Orin Nano UART Configuration for TMC2209

## 硬體連接

### Jetson Orin Nano 40-pin Header 連接

| Jetson Orin Nano | TMC2209 | 功能說明 |
|------------------|---------|----------|
| Pin 8 (UART1_TX) | RX | UART 發送 |
| Pin 10 (UART1_RX) | TX | UART 接收 |
| Pin 6 (GND) | GND | 接地 |
| Pin 11 (GPIO) | EN | 使能信號 |
| Pin 2 (5V) | VCC | 電源 |

### 電源連接

| 項目 | 規格 | 說明 |
|------|------|------|
| 邏輯電源 | 5V | 從 Jetson 5V pin 供電 |
| 馬達電源 | 12V-24V | 需要外部電源供應器 |
| 最大電流 | 1.0A | TMC2209 最大連續電流 |

## 軟體配置

### 1. 啟用 UART

```bash
# 檢查 UART 設備
ls /dev/ttyTHS*

# 如果沒有看到 ttyTHS1，需要啟用 UART1
sudo systemctl enable nvgetty
sudo systemctl start nvgetty
```

### 2. 設置權限

```bash
# 將用戶添加到 dialout 群組
sudo usermod -a -G dialout $USER

# 設置 UART 設備權限
sudo chmod 666 /dev/ttyTHS1
```

### 3. 禁用 UART 控制台

```bash
# 編輯 bootloader 配置
sudo nano /boot/extlinux/extlinux.conf

# 在 APPEND 行中移除 console=ttyTHS1,115200
# 修改前：
# APPEND ${cbootargs} quiet console=ttyTHS1,115200

# 修改後：
# APPEND ${cbootargs} quiet
```

### 4. 重啟系統

```bash
sudo reboot
```

## 測試

### 運行測試腳本

```bash
cd /home/ptri06/grating-alignment
python3 test/test_stepper.py
```

### 預期輸出

```
============================================================
TMC2209 Stepper Motor Test for NVIDIA Jetson Orin Nano
============================================================

Detected: NVIDIA Jetson Orin Nano Developer Kit

Found UART ports: ['/dev/ttyTHS1']
Testing UART port: /dev/ttyTHS1
Successfully configured UART port: /dev/ttyTHS1
Using UART port: /dev/ttyTHS1
TMC2209 stepper initialized successfully
...
✅ Test completed successfully!
TMC2209 stepper motor is working correctly on Jetson Orin Nano
============================================================
```

## 故障排除

### 1. UART 設備未找到

```bash
# 檢查設備樹
cat /proc/device-tree/chosen/plugin-manager/ids/*/uart1

# 檢查 UART 狀態
dmesg | grep ttyTHS
```

### 2. 權限問題

```bash
# 檢查用戶群組
groups $USER

# 重新登入以應用群組變更
newgrp dialout
```

### 3. 通信失敗

```bash
# 測試 UART 通信
sudo minicom -D /dev/ttyTHS1 -b 115200

# 檢查連接
sudo dmesg | grep ttyTHS1
```

### 4. GPIO 權限問題

```bash
# 檢查 GPIO 權限
ls -la /sys/class/gpio/

# 如果沒有權限，可能需要修改 udev 規則
sudo nano /etc/udev/rules.d/99-gpio.rules
```

## 性能優化

### 1. 提高 UART 波特率

```python
# 在測試腳本中可以嘗試更高的波特率
stepper = Tmc2209StepperComUartWrapperFactory.create(
    enable_pin=11,
    com_uart="/dev/ttyTHS1",
    # 其他參數...
)
```

### 2. 調整微步解析度

```python
# 更高的微步解析度提供更平滑的運動
step_resolution=32,  # 1/32 microstepping
max_step_per_second=4000,  # 更高的速度
```

## 注意事項

1. **電源要求**: 確保馬達電源供應器能夠提供足夠的電流
2. **散熱**: TMC2209 在高電流下會發熱，確保適當的散熱
3. **接地**: 確保所有接地連接良好
4. **電纜長度**: 保持 UART 連接線盡可能短，避免信號干擾
5. **電磁干擾**: 遠離高頻信號源，如 WiFi 路由器、手機等


