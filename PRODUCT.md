# Product

<!-- impeccable:product-schema 1 -->

## Platform

adaptive

## Stack

Python 3.13 with Tkinter; PyInstaller packages the Windows executable.

## Users

个人微信用户，在桌面聊天时需要快速获得、确认并手动发送回复建议。

## Product Purpose

地球online gal工具包从用户校准的微信聊天区域提取最近对话，生成可选回复，并帮助用户复制选定文本。成功是减少回复时的犹豫，同时保持用户对最终发送内容的控制。

## Positioning

它只作为桌面侧的回复建议与剪贴板助手工作，不自动向微信发送任何消息。

## Operating Context

用户在 Windows 桌面打开微信聊天窗口后，用全局快捷键或窗口按钮触发识别；工具以紧凑图形窗口展示状态、识别结果和候选回复。

## Capabilities and Constraints

- 支持聊天区域校准、OCR、DeepSeek 回复建议、关系语气切换和候选文本复制。
- 默认不保存聊天截图；调试截图必须由用户显式开启。
- API Key 只可来自系统环境变量、同目录 `.env` 或本次内存输入。
- 保留手动确认和发送边界，不实现自动发送。

## Brand Commitments

产品名为“地球online gal工具包”。用户确认希望它呈现为不显示终端的 Windows 图形工具，默认采用深色、轻量的悬浮操作窗口。

## Evidence on Hand

现有 Python OCR/DeepSeek 实现位于 `deepseek_wechat_fallback.py`；没有可复用的品牌图标、插画或照片素材。

## Product Principles

- 结果和当前状态必须一眼可读。
- 用户始终决定是否复制和发送。
- 私密聊天内容不应被默认写入磁盘。
- 配置和错误应能在工具内解决，不依赖终端阅读。
