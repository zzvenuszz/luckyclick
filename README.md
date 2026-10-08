# 🍀 LuckyClick

**LuckyClick** is a feature-rich auto clicker for Linux with virtual mouse support, point recording, and system tray integration.

**LuckyClick** là phần mềm auto click giàu tính năng dành cho Linux, hỗ trợ chuột ảo, ghi lại điểm click và tích hợp khay hệ thống.

---

<p align="center">
  <img src="https://img.shields.io/badge/version-1.1.2-brightgreen.svg" alt="Version 1.1.2"/>
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"/>
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey.svg" alt="Platform: Linux"/>
  <img src="https://img.shields.io/badge/python-3.6%2B-yellow.svg" alt="Python 3.6+"/>
  <img src="https://img.shields.io/badge/status-Beta-orange.svg" alt="Status: Beta"/>
</p>

---

## 📋 Table of Contents / Mục lục

- [Features / Tính năng](#-features--tính-năng)
- [Screenshots / Ảnh chụp màn hình](#-screenshots--ảnh-chụp-màn-hình)
- [Requirements / Yêu cầu hệ thống](#-requirements--yêu-cầu-hệ-thống)
- [Installation / Cài đặt](#-installation--cài-đặt)
  - [Install via .deb package](#1-install-via-deb-package-cài-qua-file-deb)
  - [Install from source](#2-install-from-source-cài-từ-mã-nguồn)
- [Usage / Hướng dẫn sử dụng](#-usage--hướng-dẫn-sử-dụng)
  - [Quick Start / Bắt đầu nhanh](#quick-start--bắt-đầu-nhanh)
  - [Recording Points / Ghi điểm click](#recording-points--ghi-điểm-click)
  - [Click Types / Loại click](#click-types--loại-click)
  - [Interval Configuration / Cấu hình khoảng cách](#interval-configuration--cấu-hình-khoảng-cách)
  - [Hotkeys / Phím tắt](#hotkeys--phím-tắt)
  - [Smart Click Mode / Chế độ Smart Click](#smart-click-mode--chế-độ-smart-click)
  - [Save & Load Profiles / Lưu và tải cấu hình](#save--load-profiles--lưu-và-tải-cấu-hình)
- [Project Structure / Cấu trúc dự án](#-project-structure--cấu-trúc-dự-án)
- [Building from Source / Build từ mã nguồn](#-building-from-source--build-từ-mã-nguồn)
- [Changelog / Lịch sử thay đổi](#-changelog--lịch-sử-thay-đổi)
- [License / Giấy phép](#-license--giấy-phép)
- [Author / Tác giả](#-author--tác-giả)

---

## ✨ Features / Tính năng

<details open>
<summary><strong>English 🇬🇧</strong></summary>

- **Virtual Mouse Technology** — Uses Linux `uinput` kernel module for non-blocking clicks that don't interfere with your physical mouse
- **Multiple Click Types** — Left click, right click, middle click, and double click
- **Point Recording** — Drag & drop recording with real-time coordinate display via overlay
- **Smart Click Mode** — Combine recorded clicks and keyboard shortcuts in a sequence
- **Per-action delay** — Configure a separate delay in milliseconds after every click or key action
- **Customizable Interval** — Set interval from milliseconds to hours with precision
- **Global Hotkeys** — F4 for recording mode, F8 for start/stop (fully customizable)
- **System Tray Integration** — Minimize to tray with auto-hide on start
- **Click Count Control** — Unlimited or limited number of clicks
- **Random Delay Simulation** — Add random delay percentage to simulate human behavior
- **Profile Management** — Save and load complete configurations (points, settings, hotkeys)
- **Single Instance** — Prevents multiple instances from running simultaneously
- **Bilingual Interface** — Full Vietnamese/English interface support
- **Light Theme** — Clean, modern light-themed UI with green accent colors
- **Fallback Mechanisms** — Automatically falls back to X11 or pynput if uinput is unavailable

</details>

<details>
<summary><strong>Tiếng Việt 🇻🇳</strong></summary>

- **Công nghệ chuột ảo** — Sử dụng module nhân `uinput` của Linux để click không chiếm chuột vật lý
- **Nhiều loại click** — Click chuột trái, phải, giữa và double click
- **Ghi điểm click** — Kéo thả ghi điểm với hiển thị tọa độ thời gian thực qua lớp phủ
- **Chế độ Smart Click** — Kết hợp điểm click và phím/tổ hợp phím trong cùng một chuỗi
- **Độ trễ từng thao tác** — Tùy chỉnh delay mili giây sau mỗi lần click hoặc bấm phím
- **Khoảng cách tùy chỉnh** — Đặt khoảng cách từ mili giây đến giờ với độ chính xác cao
- **Phím tắt toàn cục** — F4 để bật chế độ ghi, F8 để bắt đầu/dừng (có thể tùy chỉnh)
- **Tích hợp khay hệ thống** — Thu nhỏ xuống khay với chế độ tự động ẩn khi chạy
- **Kiểm soát số lần click** — Không giới hạn hoặc giới hạn số lần click
- **Mô phỏng độ trễ ngẫu nhiên** — Thêm phần trăm độ trễ ngẫu nhiên để mô phỏng hành vi con người
- **Quản lý cấu hình** — Lưu và tải cấu hình đầy đủ (điểm, cài đặt, phím tắt)
- **Chạy một phiên bản** — Ngăn chặn nhiều phiên bản chạy cùng lúc
- **Giao diện song ngữ** — Hỗ trợ đầy đủ giao diện Tiếng Việt/Tiếng Anh
- **Giao diện sáng** — Giao diện sạch, hiện đại với tông màu xanh lá
- **Cơ chế dự phòng** — Tự động chuyển sang X11 hoặc pynput nếu uinput không khả dụng

</details>

---

## 📸 Screenshots / Ảnh chụp màn hình
<img width="598" height="639" alt="image" src="https://github.com/user-attachments/assets/1662555d-f0ae-4815-a981-c1d736482d55" />

<img width="205" height="144" alt="image" src="https://github.com/user-attachments/assets/1cf4d44d-160b-49e0-9ffc-5e203c481893" />

## 🔧 Requirements / Yêu cầu hệ thống

| Component / Thành phần | Requirement / Yêu cầu |
|---|---|
| **Operating System** | Linux (X11 desktop environment) |
| **Python** | ≥ 3.6 |
| **PyQt5** | ≥ 5.15.0 |
| **pynput** | ≥ 1.7.0 |
| **python-xlib** | ≥ 0.33 |
| **uinput** (optional) | Kernel module for virtual mouse (recommended) |

### Install Python Dependencies / Cài đặt thư viện Python

```bash
pip install PyQt5>=5.15.0 pynput>=1.7.0 python-xlib>=0.33
```

### Enable uinput (Recommended / Khuyến nghị)

```bash
# Load the uinput kernel module / Nạp module nhân uinput
sudo modprobe uinput

# Make it persistent across reboots / Giữ cố định qua các lần khởi động
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf

# Set proper permissions / Đặt quyền truy cập
sudo chmod 666 /dev/uinput
```

> **Note:** If uinput is unavailable, LuckyClick will automatically fall back to X11 (`python-xlib`) and then to `pynput` as the last resort.
>
> **Lưu ý:** Nếu uinput không khả dụng, LuckyClick sẽ tự động chuyển sang X11 (`python-xlib`) và cuối cùng là `pynput`.

---

## 📦 Installation / Cài đặt

### 1. Install via .deb package (Cài qua file .deb)

Download the latest `.deb` package from the [Releases](https://github.com/zzvenuszz/luckyclick/releases) page, then install:

```bash
sudo dpkg -i luckyclick_1.1.2-0_all.deb
sudo apt-get install -f  # Install missing dependencies
```

### 2. Install from source (Cài từ mã nguồn)

```bash
# Clone the repository / Sao chép kho mã nguồn
git clone https://github.com/zzvenuszz/luckyclick.git
cd luckyclick

# Install the package / Cài đặt gói
pip install .
```

### Verify Installation / Kiểm tra cài đặt

```bash
luckyclick --help
```

If the command is not found after pip installation, ensure your Python scripts directory is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## 🚀 Usage / Hướng dẫn sử dụng

### Quick Start / Bắt đầu nhanh

```bash
# Launch LuckyClick / Khởi chạy LuckyClick
luckyclick
```

Or find **LuckyClick** in your application menu (look under "Utilities" or search for "LuckyClick").

Hoặc tìm **LuckyClick** trong menu ứng dụng (mục "Tiện ích" hoặc tìm kiếm "LuckyClick").

---

### Recording Points / Ghi điểm click

1. **Press F4** or click the **"Chế độ record (Record mode)"** button to enter recording mode
   
   **Nhấn F4** hoặc bấm nút **"Chế độ record (Record mode)"** để vào chế độ ghi

2. The main window will be temporarily hidden and a transparent overlay will appear. **Drag** from the overlay to any position to record a click point. Recording cannot be started while auto-click is running.
   
   Cửa sổ chính sẽ tạm ẩn và một lớp phủ trong suốt xuất hiện. **Kéo thả** từ overlay đến vị trí bất kỳ để ghi điểm click. Không thể bật chế độ record khi auto click đang chạy.

3. The recorded point will appear in the list with its coordinates and click type. Each new action starts with a 1000 ms delay; edit the value or use the spin buttons to change it.
   
   Điểm đã ghi sẽ xuất hiện trong danh sách kèm tọa độ và loại click. Mỗi thao tác mới có delay mặc định 1000 ms; sửa trực tiếp giá trị hoặc dùng nút tăng/giảm.

4. Use **"Thêm phím"** to capture a single key (such as F5) or a combination (such as Ctrl+A or Ctrl+Shift+A) and add it to the sequence.

   Dùng nút **"Thêm phím"** để ghi một phím (ví dụ F5) hoặc tổ hợp phím (ví dụ Ctrl+A, Ctrl+Shift+A) vào chuỗi.

5. **Press F4** again or click the button to exit recording mode

   **Nhấn F4** lần nữa hoặc bấm nút để thoát chế độ ghi

---

### Click Types / Loại click

| Type / Loại | Description / Mô tả |
|---|---|
| 🖱 **Left** / Chuột trái | Standard left click |
| 🖱 **Right** / Chuột phải | Context menu click |
| 🖱 **Middle** / Chuột giữa | Scroll wheel click |
| 🔄 **Double** | Double left click |

---

### Interval Configuration / Cấu hình khoảng cách

Configure the time between clicks using hours, minutes, seconds, and milliseconds:

Cấu hình thời gian giữa các lần click bằng giờ, phút, giây và mili giây:

- **Minimum / Tối thiểu:** 10 ms
- **Maximum / Tối đa:** 99h 59m 59s 999ms

Add **random delay** (0-100%) to make intervals appear more natural:

Thêm **độ trễ ngẫu nhiên** (0-100%) để khoảng cách trông tự nhiên hơn:

```
Actual Interval = Base Interval ± Random(0, Base Interval × RandomDelay%)
```

---

### Hotkeys / Phím tắt

| Hotkey / Phím tắt | Action / Hành động |
|---|---|
| **F4** | Toggle recording mode / Bật/tắt chế độ ghi |
| **F8** (default / mặc định) | Start/Stop auto click / Bắt đầu/Dừng auto click |
| **Custom / Tùy chỉnh** | Select "Tùy chỉnh (Custom)" in the dropdown and press your desired key |

> **Note:** Hotkeys work globally, even when LuckyClick is minimized to the system tray.
>
> **Lưu ý:** Phím tắt hoạt động toàn cục, ngay cả khi LuckyClick được thu nhỏ xuống khay hệ thống.

---

### Smart Click Mode / Chế độ Smart Click

When **Smart Click** is enabled, the recorded click and key actions run in order. Each row can have its own delay. Enable **Smart Delay** to apply each row's delay; otherwise, the global interval is used for every action.

Khi bật **Smart Click**, các click và phím đã ghi được thực hiện theo thứ tự. Mỗi dòng có thể có delay riêng. Bật **Áp dụng Smart Delay** để dùng delay của từng dòng; nếu tắt, mọi thao tác dùng khoảng cách global.

```
Point 1:  X: 500  Y: 300  🖱 (Left click / Chuột trái)
Point 2:  Ctrl+A
Point 3:  X: 800  Y: 400  🔄 (Double click)
```

When Smart Click is **disabled**, all clicks use the global click type selected in the dropdown.

Khi Smart Click **tắt**, tất cả click đều dùng loại click chung được chọn trong dropdown.

---

### Save & Load Profiles / Lưu và tải cấu hình

Save your entire configuration (points, interval, click type, hotkey, etc.) to a JSON file:

Lưu toàn bộ cấu hình (điểm, khoảng cách, loại click, phím tắt...) vào file JSON:

- Click **"Lưu profile (Save)"** to save
- Click **"Tải profile (Load)"** to load a previously saved profile

---

## 📁 Project Structure / Cấu trúc dự án

```
luckyclick/
├── luckyclick/                    # Main package / Gói chính
│   ├── __init__.py
│   ├── main.py                    # Entry point / Điểm vào chính
│   ├── icon.png                   # Application icon
│   ├── core/                      # Core logic module
│   │   ├── __init__.py
│   │   ├── clicker.py             # Auto click engine (uinput, X11, pynput)
│   │   ├── hotkey_manager.py      # Global hotkey management
│   │   ├── recorder.py            # Point recording
│   │   └── wm_detector.py         # Window manager detection
│   ├── gui/                       # GUI module
│   │   ├── __init__.py
│   │   ├── click_effect.py        # Visual click effects
│   │   ├── main_window.py         # Main application window
│   │   └── overlay.py             # Transparent recording overlay
│   └── resources/
│       └── icons/                 # Application icons
├── build/                         # Build output directory
├── debian/                        # Debian packaging files
├── setup.py                       # Python package setup
├── Makefile                       # Build automation
├── generate_icons.py              # Icon generation script
└── luckyclick.desktop             # Desktop entry file
```

---

## 🔨 Building from Source / Build từ mã nguồn

### Build .deb Package / Tạo gói .deb

```bash
# Install build dependencies / Cài đặt công cụ build
sudo apt-get install devscripts debhelper python3-all python3-setuptools

# Build the package / Build gói
make deb

# Output file / File đầu ra: luckyclick_1.1.2-0_all.deb
```

### Manual Build Steps / Các bước build thủ công

```bash
# 1. Create directory structure / Tạo cấu trúc thư mục
mkdir -p build/luckyclick_1.1.2-0_all/DEBIAN
mkdir -p build/luckyclick_1.1.2-0_all/usr/bin
mkdir -p build/luckyclick_1.1.2-0_all/usr/share/luckyclick
mkdir -p build/luckyclick_1.1.2-0_all/usr/share/applications
mkdir -p build/luckyclick_1.1.2-0_all/usr/share/icons/hicolor/{16x16,32x32,48x48,64x64,128x128,256x256}/apps

# 2. Copy application files / Sao chép file ứng dụng
cp -r luckyclick build/luckyclick_1.1.2-0_all/usr/share/luckyclick/
cp luckyclick.desktop build/luckyclick_1.1.2-0_all/usr/share/applications/
cp debian/control build/luckyclick_1.1.2-0_all/DEBIAN/
cp debian/postinst build/luckyclick_1.1.2-0_all/DEBIAN/
cp debian/postrm build/luckyclick_1.1.2-0_all/DEBIAN/

# 3. Generate icons / Tạo icon
python generate_icons.py

# 4. Build the .deb / Build file .deb
dpkg-deb --build build/luckyclick_1.1.2-0_all
```

---

## 📝 Changelog / Lịch sử thay đổi

### Version 1.1.2 (Latest / Mới nhất)

**New Features / Tính năng mới:**
- Smart Click mode — configurable per-action delays and keyboard shortcuts
- Single-key and key-combination actions in recorded sequences
- Custom hotkey capture — assign any key as start/stop hotkey
- Click at cursor position (normal mode without recorded points)
- Unlimited click count option

**Improvements / Cải tiến:**
- Better error handling and fallback mechanisms
- Enhanced logging with rotation
- Dynamic hotkey re-registration without restart
- Improved HiDPI display support

**Bug Fixes / Sửa lỗi:**
- Fixed single-instance detection race condition
- Fixed PID file cleanup on crash
- Fixed overlay coordinate calculation on multi-monitor setups

### Version 1.0.0

- Initial release with core auto clicker functionality
- Virtual mouse support via uinput
- Point recording with drag & drop overlay
- Global hotkeys (F4, F8)
- System tray integration
- Bilingual interface (Vietnamese/English)
- Save/load profiles
- Random delay simulation

---

## 📄 License / Giấy phép

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Dự án này được cấp phép theo **Giấy phép MIT** — xem file [LICENSE](LICENSE) để biết chi tiết.

```
MIT License

Copyright (c) 2024 LuckyClick Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 👤 Author / Tác giả

**LuckyClick Team**

- GitHub: [@zzvenuszz](https://github.com/zzvenuszz)
- Repository: [https://github.com/zzvenuszz/luckyclick](https://github.com/zzvenuszz/luckyclick)

---

<p align="center">
  Make with ❤️ for the Linux community<br>
  <sub>Dành tặng cho cộng đồng Linux ❤️</sub>
</p>
