#!/usr/bin/env python3
"""fc_card.py —— 截取 FC 游戏的标题画面和游戏画面，生成一张“收藏卡”封面。

卡片样式（600×840）：
    ┌──────────────────────────┐
    │ FC · 汉化收藏   SimUI 收藏卡 │  顶栏
    │                          │
    │      游戏标题标志（自动裁切）    │  从标题画面裁出
    │                          │
    │  ┌──────────────────┐    │
    │  │     游戏画面          │    │  实机游戏画面
    │  └──────────────────┘    │
    │ 游戏名            汉化版本    │  底栏
    └──────────────────────────┘

两种用法
1) 直接用模拟器截图（需要汉化工具包 hanhua_kit，里面有 hhkit/ 和 emus/）：
   python3 fc_card.py 游戏.nes --kit /path/hanhua_kit --name 赤色要塞 --sub 雷精灵汉化版 \
       --title-at 90 --keys "start,w200,start*8,w60" --play "up+b:300"

2) 已经有截图，只做卡片（不需要工具包）：
   python3 fc_card.py --title-img title.png --play-img play.png --name 赤色要塞 --sub 雷精灵汉化版

参数
  --title-at N     开机后第 N 帧截标题画面（默认 120；60 帧 = 1 秒）
  --title-keys S   标题需要按键才出现时，用按键脚本代替 --title-at，如 "w300,h10:start,w200"
  --keys S         截完标题后进入游戏的按键脚本（hhkit 语法）：
                   w60 等 60 帧；start 按一下；a*3 连按 3 次；a+b 同时按；h30:right 按住 30 帧
  --play K:N       进游戏后按住 K 再跑 N 帧截游戏画面，如 "right+b:240"（默认 "right:180"）
  --state F        截完标题后读入存档，直接跳到想截的游戏场景（支持 FCEUX 的 .fcs，自动转换）
  --logo x0,y0,x1,y1   手动指定标志区域（默认自动识别）
  --accent #rrggbb     强调色（默认从标志里自动取）
  --label 文字      顶栏左侧文字（默认“FC · 汉化收藏”）
  -o 输出.png       默认 <name>_card.png；同时保存 <name>_title.png、<name>_play.png 原始截图

实测例子（K 为 hanhua_kit 目录）
  # 标题在开机 1.5 秒时出现；进游戏后开车向上射击
  python3 fc_card.py 赤色要塞.nes --kit $K --name 赤色要塞 --sub 雷精灵汉化版 \
      --title-at 90 --keys "start,w200,start*8,w60,h240:up+b" --play "up+b:200"
  # 标题开机就有；再读 FCEUX 存档跳到选人画面，选人开始后边走边打
  python3 fc_card.py 魂斗罗力量.nes --kit $K --name "魂斗罗 力量" --sub "DMG 汉化 v1.2" \
      --title-at 120 --state 魂斗罗力量.fcs --keys "h6:right,w40,h6:start,w240,h300:right+b" --play "right+b:120"
  # 汉化标题要跳过开场后按开始才出现，所以用 --title-keys
  python3 fc_card.py 古巴战士.nes --kit $K --name 古巴战士 --sub 惊风汉化版 \
      --title-keys "w300,h10:start,w200,h10:start,w350,h6:start,w180" \
      --keys "h6:start,w60,h6:start,w300,h300:up+b" --play "up+b:60"
  python3 fc_card.py 救火英雄.nes --kit $K --name 救火英雄 --sub "Cslrxyz 汉化 hack 版" \
      --title-at 100 --keys "h10:start,w200,h10:start,w200,h300:right+a" --play "a:60"

  不知道开场要多久、按什么键时，先把 --keys 留空，看生成的 *_play.png 是哪个画面，再逐步加按键。
  菜单不认短按时，用 h6:start（按住 6 帧）代替 start。

依赖：Python 3.9+、Pillow（pip install pillow）。
"""
import argparse
import os
import struct
import sys
import zlib
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf',
    '/System/Library/Fonts/PingFang.ttc',
]


# ------------------------------------------------------------------ 截图

def capture(rom, kit, title_at, keys, play, state=None, title_keys=None):
    """用工具包的模拟器运行 ROM，返回 (标题画面, 游戏画面) 两张 PIL 图（原始分辨率 256×240）。"""
    kit = kit or os.environ.get('HHKIT_DIR')
    if not kit or not os.path.isdir(os.path.join(kit, 'hhkit')):
        sys.exit('需要汉化工具包：用 --kit 指定 hanhua_kit 目录（或设环境变量 HHKIT_DIR）')
    sys.path.insert(0, os.path.abspath(kit))
    from hhkit import emu

    c = emu.open(rom)
    # 1) 标题画面：开机后等 title_at 帧，或按 title_keys 脚本操作到标题出现
    if title_keys:
        c.script(title_keys)
    else:
        c.run(title_at)
    title = c.image().convert('RGB')

    # 2) 进入游戏：可先读存档跳到指定场景，再执行按键脚本
    if state:
        raw = open(state, 'rb').read()
        if raw[:4] == b'FCSX':                       # FCEUX 存档 → 内核存档
            raw = fceux_to_core(raw, c.save_state())
        c.load_state(raw)
        c.run(2)
    if keys:
        c.script(keys)
    btn, frames = (play.split(':') + ['180'])[:2] if play else ('', '0')
    c.run(int(frames), [b for b in btn.split('+') if b])
    c.run(4)
    return title, c.image().convert('RGB')


def fceux_to_core(fcs, template):
    """FCEUX 2.x 的 .fcs（FCSX）存档 → fceumm 内核存档：同段同名的数据块逐个搬过去。"""
    def sections(data):
        out, p = [], 0
        while p + 5 <= len(data):
            t, size = data[p], struct.unpack('<I', data[p + 1:p + 5])[0]
            body, p = data[p + 5:p + 5 + size], p + 5 + size
            ch, q = [], 0
            while q + 8 <= len(body):
                n, cs = body[q:q + 4], struct.unpack('<I', body[q + 4:q + 8])[0]
                ch.append((n, body[q + 8:q + 8 + cs])); q += 8 + cs
            out.append((t, ch))
        return out

    clen = struct.unpack('<I', fcs[12:16])[0]
    payload = zlib.decompress(fcs[16:16 + clen]) if clen not in (0, 0xFFFFFFFF) else fcs[16:]
    src = {(t, n): d for t, ch in sections(payload) for n, d in ch}
    body = b''
    for t, ch in sections(template[16:]):
        blk = b''
        for n, d in ch:
            s = src.get((t, n))
            d = d if s is None else (s if len(s) == len(d) else (s + d)[:len(d)])
            blk += n + struct.pack('<I', len(d)) + d
        body += bytes([t]) + struct.pack('<I', len(blk)) + blk
    out = template[:4] + struct.pack('<I', len(body)) + template[8:16] + body
    return out + b'\0' * max(0, len(template) - len(out))


# ------------------------------------------------------------------ 卡片

def auto_logo_box(im, gap=6, join=10, pad=6):
    """自动找标题标志：
    1. 背景色 = 画面四边最常见的颜色；
    2. 按“连续 gap 行以上没有前景像素”把画面切成若干横条；
    3. 取前景像素最多的横条当标志，与它相距不超过 join 行、且不比它宽的横条一并纳入
       （例如标志上方的厂商名）；菜单、版权行通常离得远或很窄，会被排除。"""
    w, h = im.size
    edge = [im.getpixel((x, 0)) for x in range(w)] + [im.getpixel((x, h - 1)) for x in range(w)] + \
           [im.getpixel((0, y)) for y in range(h)] + [im.getpixel((w - 1, y)) for y in range(h)]
    bg = Counter(edge).most_common(1)[0][0]
    fg = lambda p: abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 60
    rows = [[x for x in range(w) if fg(im.getpixel((x, y)))] for y in range(h)]

    bands, cur, empty = [], None, 0          # 每条：[y0, y1, 像素数, x0, x1]
    for y, xs in enumerate(rows):
        if xs:
            if cur is None:
                cur = [y, y, 0, w, 0]
            cur[1] = y; cur[2] += len(xs); cur[3] = min(cur[3], xs[0]); cur[4] = max(cur[4], xs[-1])
            empty = 0
        elif cur is not None:
            empty += 1
            if empty >= gap:
                bands.append(cur); cur = None
    if cur is not None:
        bands.append(cur)
    if not bands:
        return 0, 0, w, h

    i = max(range(len(bands)), key=lambda k: bands[k][2])
    y0, y1, _, x0, x1 = bands[i]
    width = x1 - x0
    for k in list(range(i - 1, -1, -1)) + list(range(i + 1, len(bands))):
        b = bands[k]
        near = (b[1] < y0 and y0 - b[1] <= join) or (b[0] > y1 and b[0] - y1 <= join)
        if near and b[4] - b[3] <= width:
            y0, y1, x0, x1 = min(y0, b[0]), max(y1, b[1]), min(x0, b[3]), max(x1, b[4])
    return max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad + 1), min(h, y1 + pad + 1)


def auto_accent(im):
    """标志里出现最多的“鲜艳颜色”做强调色。"""
    best, score = (220, 160, 60), -1
    for (r, g, b), n in Counter(im.getdata()).most_common(64):
        mx, mn = max(r, g, b), min(r, g, b)
        sat = (mx - mn) / mx if mx else 0
        if mx >= 90 and sat >= 0.35 and n * sat > score:
            best, score = (r, g, b), n * sat
    return best


def make_card(title, play, name, sub='', label='FC · 汉化收藏', logo_box=None, accent=None, font=None):
    font = font or next((f for f in FONTS if os.path.exists(f)), None)
    if not font:
        sys.exit('找不到中文字体，用 --font 指定')
    F = lambda n: ImageFont.truetype(font, n)
    up = lambda im, k: im.resize((im.width * k, im.height * k), Image.NEAREST)   # 像素画整数倍放大

    logo = title.crop(logo_box or auto_logo_box(title))
    accent = accent or auto_accent(logo)

    W, H = 600, 840
    card = Image.new('RGB', (W, H), (16, 15, 18))
    d = ImageDraw.Draw(card)

    # 标题标志：整数倍放大，居中放在上半部分
    k = max(1, min((W - 40) // logo.width, 330 // logo.height))
    lg = up(logo, k)
    card.paste(lg, ((W - lg.width) // 2, 70 + (330 - lg.height) // 2))

    # 游戏画面：去掉顶部 10 行（常有残影），放大后加强调色边框
    sn = up(play, 2).crop((0, 20, play.width * 2, min(play.height * 2, 380)))
    sn = sn.resize((520, int(520 * sn.height / sn.width)), Image.NEAREST)
    x, y = (W - sn.width) // 2, 420
    card.paste(sn, (x, y))
    d.rectangle([x - 3, y - 3, x + sn.width + 2, y + sn.height + 2], outline=accent, width=3)

    # 顶栏、底栏
    d.rectangle([0, 0, W, 48], fill=(0, 0, 0)); d.rectangle([0, 48, W, 52], fill=accent)
    d.text((22, 24), label, font=F(24), fill=(235, 235, 235), anchor='lm')
    d.text((W - 22, 24), 'SimUI 收藏卡', font=F(18), fill=(150, 150, 150), anchor='rm')
    d.rectangle([0, H - 80, W, H], fill=(0, 0, 0)); d.rectangle([0, H - 84, W, H - 80], fill=accent)
    d.text((22, H - 40), name, font=F(34), fill=(255, 255, 255), anchor='lm')
    if sub:
        d.text((W - 22, H - 40), sub, font=F(22), fill=accent, anchor='rm')
    return card


# ------------------------------------------------------------------ 命令行

def main():
    ap = argparse.ArgumentParser(description='截取 FC 游戏标题与游戏画面，生成收藏卡封面',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('rom', nargs='?', help='.nes 文件（用 --title-img/--play-img 时可省略）')
    ap.add_argument('--kit', help='hanhua_kit 目录')
    ap.add_argument('--name', required=True, help='游戏名（显示在底栏）')
    ap.add_argument('--sub', default='', help='底栏右侧小字，如“雷精灵汉化版”')
    ap.add_argument('--label', default='FC · 汉化收藏')
    ap.add_argument('--title-at', type=int, default=120)
    ap.add_argument('--title-keys')
    ap.add_argument('--keys', default='start,w200,start*6,w60')
    ap.add_argument('--play', default='right:180')
    ap.add_argument('--state')
    ap.add_argument('--title-img'); ap.add_argument('--play-img')
    ap.add_argument('--logo', help='x0,y0,x1,y1')
    ap.add_argument('--accent', help='#rrggbb')
    ap.add_argument('--font')
    ap.add_argument('-o', '--out')
    a = ap.parse_args()

    if a.title_img and a.play_img:
        title, play = Image.open(a.title_img).convert('RGB'), Image.open(a.play_img).convert('RGB')
    elif a.rom:
        title, play = capture(a.rom, a.kit, a.title_at, a.keys, a.play, a.state, a.title_keys)
        base = os.path.splitext(a.out or a.name + '_card.png')[0].removesuffix('_card')
        title.save(base + '_title.png'); play.save(base + '_play.png')
    else:
        ap.error('需要 ROM，或者同时给 --title-img 和 --play-img')

    box = tuple(int(v) for v in a.logo.split(',')) if a.logo else None
    acc = tuple(int(a.accent.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) if a.accent else None
    out = a.out or a.name + '_card.png'
    make_card(title, play, a.name, a.sub, a.label, box, acc, a.font).save(out)
    print('收藏卡：', out)


if __name__ == '__main__':
    main()
