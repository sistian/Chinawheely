#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""headless Chrome 视觉回归对比：修复前 vs 修复后（成对比较）。

用法：
    python3 tools/cw_visual_check.py --pairs A.html B.html C.html D.html ...
    （两两一组：前=修复前，后=修复后）

每组做三件事：
  1) 两份文件各截 2 次图 → 取像素级「最接近」的一次组合，降低动画/时序噪声
  2) 逐像素比较，差异按通道阈值（默认 12/255）判定，忽略抗锯齿/阴影微差
  3) 同时报告「同文件自比」的基线噪声（同样流程跑一遍自己），用于判断
     剩余差异是否只是截图抖动

退出码：0 = 全部组无实质差异；1 = 有实质差异
"""
import os
import subprocess
import sys
import zlib
import struct

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
THRESHOLD = 12          # 通道差 ≤ 该值视为噪声
SIG = 6                 # 超过该通道差才算实质差异像素


def png_pixels(path):
    data = open(path, 'rb').read()
    pos = 8
    idat = b''
    w = h = bitd = ctype = None
    interlace = 0
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, bitd, ctype = struct.unpack('>IIBB', chunk[:10])
            interlace = chunk[12]
        elif typ == b'IDAT':
            idat += chunk
        elif typ == b'IEND':
            break
        pos += 12 + ln
    if bitd != 8 or interlace != 0:
        return None
    nch = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
    if nch is None:
        return None
    raw = zlib.decompress(idat)
    stride = w * nch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, nch, bytes(out)


def shot(src, outpng, width=1280, height=900):
    if os.path.exists(outpng):
        os.remove(outpng)
    url = 'file://' + os.path.abspath(src)
    cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
           f'--window-size={width},{height}', f'--screenshot={outpng}',
           '--virtual-time-budget=8000', '--no-sandbox',
           '--force-prefers-reduced-motion', url]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return False
    return os.path.exists(outpng)


def diff_count(a, b):
    """返回 (实质差异像素数, 最大通道差)"""
    wa, ha, na, pa = a
    wb, hb, nb, pb = b
    if (wa, ha) != (wb, hb):
        return -1, 255
    n = 0
    mx = 0
    for i in range(0, len(pa), na):
        d = 0
        for k in range(min(na, nb)):
            dv = pa[i + k] - pb[i + k]
            if dv < 0:
                dv = -dv
            if dv > d:
                d = dv
        if d > mx:
            mx = d
        if d > SIG:
            n += 1
    return n, mx


def best_pair(pa_list, pb_list):
    """在多张截图里找差异最小的一对"""
    best = None
    for x in pa_list:
        for y in pb_list:
            if x is None or y is None:
                continue
            d, mx = diff_count(x, y)
            if best is None or (d >= 0 and d < best[0]):
                best = (d, mx, x, y)
    return best


def shoot_set(path, tag, n=2):
    out = []
    for i in range(n):
        p = f'/tmp/cw_shots/{tag}_{i}.png'
        if shot(path, p):
            out.append(png_pixels(p))
        else:
            out.append(None)
    return out


def main():
    args = sys.argv[1:]
    if args and args[0] == '--pairs':
        args = args[1:]
    if len(args) < 2 or len(args) % 2:
        print('用法: python3 tools/cw_visual_check.py --pairs A.html B.html ...')
        return 2
    os.makedirs('/tmp/cw_shots', exist_ok=True)
    allok = True
    for i in range(0, len(args), 2):
        bf, af = args[i], args[i + 1]
        before = shoot_set(bf, 'b' + str(i))
        after = shoot_set(af, 'a' + str(i))
        if not before or not after or before[0] is None or after[0] is None:
            print(f'{bf} -> {af}: ❌ 截图失败')
            allok = False
            continue
        d, mx, _, _ = best_pair(before, after)
        total = before[0][0] * before[0][1]
        if d < 0:
            print(f'{bf} -> {af}: ❌ 尺寸不同')
            allok = False
            continue
        # 基线：after 自己和自己比（同一文件截两次的噪声）
        bd, bmx, _, _ = best_pair(after, after[::-1]) if len(after) > 1 else (0, 0, None, None)
        verdict = '✅ 无实质差异' if d == 0 else (
            '⚠️ 差异在基线噪声内' if d <= bd else '❌ 有实质差异')
        if d > bd:
            allok = False
        print(f'{bf} -> {af}: {verdict}  实质差异 {d}/{total} ({d * 100.0 / total:.4f}%)'
              f'  最大通道差 {mx}  |  自比基线 {bd} (最大通道差 {bmx})')
    print('\n结论：' + ('视觉零回归 ✅' if allok else '存在实质差异，需复查 ⚠️'))
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
