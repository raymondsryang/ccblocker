#!/bin/bash

# 用PyInstaller将python文件打包成Mac M系列芯片的可执行程序，添加应用图标
# 替换 main.py 为你的Python源码文件名
TARGET=main.py
OUTNAME=ccblocker
ICON=icon.icns    # 你的图标文件

pyinstaller --onefile --windowed -n "$OUTNAME" --icon "$ICON" "$TARGET"

echo "已打包到 dist/$OUTNAME"