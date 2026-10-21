[← Systems](../systems.md)

# 从视觉事件到嵌入式控制

慧眼识珠综合实验分为视觉/工业控制与 i.MX6ULL 两个工程入口。我的工作包括 OpenCV 视觉链路、Linux 控制器与 HMI、接口规范、系统集成和真机验收；PLC 部分参与开发与联调，由团队协作完成。

## 两条后端，同一个识别入口

| 路线 | 处理链 | 工程入口 |
|---|---|---|
| 视觉 + PLC | Windows / OpenCV → 事件 → S7 数据区 → FIFO → 按键 / 1–3 盏灯 | [视觉综合实验](https://github.com/lls144/huiyan-shizhu) |
| 嵌入式 Linux | Windows / OpenCV → TCP JSON Lines → i.MX6ULL FIFO / 三工位 FSM → KEY / RGB / LCD | [i.MX6ULL 控制与 HMI](https://github.com/lls144/huiyan-shizhu-imx6ull) |

视觉运行在 PC；i.MX6ULL 承担控制、输入输出和 HMI。GUI 中的传送带与分流动作用于演示，实体反馈是按键、LED 和 LCD。

## 一次遮挡，不应该变成第二个物体

Linux 路线的 Windows 真机测试中，手部短暂遮挡让旧 tracker 连续丢失目标，提前产生 EXIT。目标再次可见时得到新 ID，随后又入队一次。

修订后，为已确认目标保留 25 帧恢复窗口，并同时检查类别与空间匹配。真实相机复测中，同一物体在遮挡前后保留 ID，只入队一次；真正移出并超过窗口后，再进入才生成新 ID。具体条件、日志摘要和回归入口见 [TEST-017](https://github.com/lls144/huiyan-shizhu-imx6ull/blob/master/notes/tests/TEST-017-Windows-Vision-Occlusion-Lifecycle-Robustness.md)。

## 让界面跟随控制器

PC GUI 和板端 HMI 都读取控制器状态，而不是根据视觉列表自行推演 FIFO。三工位只推进队首；错误工位按键不改变队列。LCD Reset 调用控制器协议，状态回读后更新界面；会话计数按分拣序号去重。

实际记录覆盖相机事件经 TCP 入队、实体 KEY1/2/3、RGB、800×480 LCD / Goodix Reset、服务断连恢复及冷启动。协议、运行步骤和每项验证范围分别放在两个仓库的技术文档中。

[阅读视觉与 PLC 工程](https://github.com/lls144/huiyan-shizhu) · [阅读 Linux 部署与验收](https://github.com/lls144/huiyan-shizhu-imx6ull)
