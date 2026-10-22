[← 首页](README.md)

# Embedded & System Integration

## 基于 OpenCV 的视觉分拣与双后端控制系统

Windows 上的 OpenCV 负责识别、ROI 与目标生命周期；控制后端分别采用 PLC 和 i.MX6ULL。Linux 路线通过 TCP JSON Lines 连接 FIFO、三工位 FSM、实体按键、RGB 与 LCD HMI。

我负责视觉、Linux 控制器/HMI、接口规范、集成和真机验收，参与 PLC 开发与调试。

- [工程案例：从视觉事件到嵌入式控制](projects/embedded-linux-vision.md)
- [视觉综合实验 / PLC 集成](https://github.com/lls144/huiyan-shizhu)
- [i.MX6ULL / 控制器与 HMI](https://github.com/lls144/huiyan-shizhu-imx6ull)

## 其他实践

| 方向 | 实际工作 |
|---|---|
| STM32 / Embedded C | 电源控制中的 HRTIM、ADC/DMA、PWM、CAN 与板卡联调 |
| RK3566 | 基于参考板进行外围电源/接口、I²C 触摸设备树、系统烧录及存储扩容调试 |
| K230 / MSPM0 | K230 Linux 视觉部署与 UART 坐标通信，配合 MSPM0 云台控制和按键板 |
| K210 / STM32 | 整车 PCB 设计 |
| 点云工具 | Python / Open3D / PySide6 处理链；C++ / Qt / PCL / VTK 查看器探索，两者实现范围分别记录 |

这些方向暂不堆叠项目数量；有完整资料与可公开证据后再扩展独立档案。
