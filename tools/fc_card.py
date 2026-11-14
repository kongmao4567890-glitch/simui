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

三种用法
1) 全自动（任何游戏都可以先这样试）：只给 ROM 和名字
   python3 fc_card.py 游戏.nes --kit /path/hanhua_kit --name 赤色要塞 --sub 雷精灵汉化版
   · 标题：从开机起持续观察，挑“停留最久、颜色丰富、纯色背景上有标志”的静止画面；
           厂商 Logo、剧情文字颜色少会被排除；开场太长会自动按一次开始键跳过。
   · 游戏画面：先观察不按键时的自动演示，再轮流用“开始 / 右+开始 / 下+开始 / A”进入游戏，
           模拟“方向 + 攻击”，挑“画面在动、颜色丰富、和标题不同”的帧。
   · 同时输出 <名字>_candidates.png：标题候选、游戏画面候选各一排，带编号。

2) 自动选得不满意：看候选总览，用编号换一张（模拟器每次运行结果相同，编号固定）
   python3 fc_card.py 游戏.nes --kit ... --name ... --title-pick 3 --play-pick 2

3) 流程特殊的游戏（要选人、要读存档等）：手动写按键脚本，可与自动找标题混用
   python3 fc_card.py 游戏.nes --kit ... --name ... --title-pick 3 \
       --state 存档.fcs --keys "h6:right,w40,h6:start,w240" --play "right+b:120"

   已经有截图，只做卡片（不需要工具包）：
   python3 fc_card.py --title-img title.png --play-img play.png --name 赤色要塞 --sub 雷精灵汉化版

参数
  （以下截图参数都可省略，省略即自动）
  --title-pick N   自动模式下改用第 N 个标题候选；--play-pick N 同理（游戏画面）
  --scan 秒        自动找标题时最多观察多少秒（默认 40）
  --title-at N     开机后第 N 帧截标题画面（60 帧 = 1 秒）
  --title-keys S   标题需要按键才出现时，用按键脚本代替 --title-at，如 "w300,h10:start,w200"
  --keys S         截完标题后进入游戏的按键脚本（hhkit 语法）：
                   w60 等 60 帧；start 按一下；a*3 连按 3 次；a+b 同时按；h30:right 按住 30 帧
  --play K:N       进游戏后按住 K 再跑 N 帧截游戏画面，如 "right+b:240"
  --state F        截完标题后读入存档，直接跳到想截的游戏场景（支持 FCEUX 的 .fcs，自动转换）
  --logo x0,y0,x1,y1   手动指定标志区域（默认自动识别）
  --accent #rrggbb     强调色（默认从标志里自动取）
  --label 文字      顶栏文字，默认按扩展名：FC / SFC / MD / GBA / GB … · 汉化收藏
  -o 输出.png       默认 <name>_card.png；同时保存 <name>_title.png、<name>_play.png 原始截图
                   和 <name>_candidates.png 候选总览

手写按键的实测例子（K 为 hanhua_kit 目录；赤色要塞、古巴战士、救火英雄用全自动即可）
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

  建议先全自动跑一次，看 *_candidates.png；候选里有合适的就用 --title-pick / --play-pick，
  都不合适再写 --keys。
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

def open_core(rom, kit):
    kit = kit or os.environ.get('HHKIT_DIR')
    if not kit or not os.path.isdir(os.path.join(kit, 'hhkit')):
        sys.exit('需要汉化工具包：用 --kit 指定 hanhua_kit 目录（或设环境变量 HHKIT_DIR）')
    sys.path.insert(0, os.path.abspath(kit))
    from hhkit import emu
    return emu.open(rom)


def load_state_file(c, path):
    raw = open(path, 'rb').read()
    if raw[:4] == b'FCSX':                       # FCEUX 存档 → 内核存档
        raw = fceux_to_core(raw, c.save_state())
    c.load_state(raw)
    c.run(2)


def capture(rom, kit, title_at=None, keys=None, play=None, state=None, title_keys=None, scan=40, verbose=True,
            title_pick=1, play_pick=1, sheet=None):
    """运行 ROM，返回 (标题画面, 游戏画面)。
    没有给 title_at / title_keys 时自动找标题；没有给 keys / play 时自动找游戏画面。"""
    c = open_core(rom, kit)
    log = print if verbose else (lambda *a: None)

    # 1) 标题画面
    t_cands = None
    if title_keys:
        c.script(title_keys); title = c.image().convert('RGB')
    elif title_at is not None:
        c.run(title_at); title = c.image().convert('RGB')
    else:
        t_cands = auto_title(c, scan)
        title, f, st, _ = t_cands[0]
        c.load_state(st)

    # 2) 游戏画面
    p_cands = None
    if state:
        load_state_file(c, state)
    if keys or play:
        if keys:
            c.script(keys)
        btn, frames = (play.split(':') + ['180'])[:2] if play else ('', '60')
        c.run(int(frames), [b for b in btn.split('+') if b])
        c.run(4)
        shot = c.image().convert('RGB')
    else:
        p_cands = auto_play(c, title)
        k = min(max(play_pick, 1), len(p_cands)) - 1
        shot, f, how = p_cands[k]
        log('游戏画面：第 %d 帧，%s（候选 %d/%d）' % (f, how, k + 1, len(p_cands)))

    # 3) 标题候选重新排序：和游戏画面很像的、或在候选里有相似同伴的（多半是自动演示），降分
    if t_cands:
        plays = [x[0] for x in (p_cands or [])] + [shot]
        def rescore(t):
            near = min(frame_diff(t[0], p) for p in plays)
            # 自动演示会在同一场景停好几次，候选里有“相似同伴”；标题画面通常独一无二
            colors, content = frame_info(t[0])
            twins = sum(1 for o in t_cands if o is not t and frame_diff(t[0], o[0]) < 25)
            demo_like = twins and content > 0.55            # 满屏场景且有相似同伴：多半是自动演示
            text_only = colors < 5                          # 版权页、汉化组说明等纯文字画面
            return t[3] * (0.25 if near < 20 else 1.0) * (0.4 if demo_like else 1.0) * (0.3 if text_only else 1.0)
        scored = sorted(((rescore(t), t) for t in t_cands), key=lambda x: x[0], reverse=True)
        t_cands[:] = [t for _, t in scored]
        log('标题候选得分：' + '，'.join('第%d帧=%.1f' % (t[1], sc) for sc, t in scored))
        k = min(max(title_pick, 1), len(t_cands)) - 1
        title, f = t_cands[k][0], t_cands[k][1]
        log('标题画面：第 %d 帧（候选 %d/%d）' % (f, k + 1, len(t_cands)))

    if sheet and (t_cands or p_cands):
        candidates_sheet(t_cands or [(title, 0)], p_cands or [(shot, 0)], sheet)
        log('候选总览：%s（不满意可加 --title-pick N / --play-pick N 换一张）' % sheet)
    return title, shot


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


# ------------------------------------------------------------------ 自动识别

def _small(im):
    return im.convert('RGB').resize((64, 60), Image.NEAREST)


def frame_info(im):
    """画面特征：颜色数、非背景比例（背景 = 最常见颜色）。"""
    sm = _small(im)
    px = list(sm.get_flattened_data()) if hasattr(sm, 'get_flattened_data') else list(sm.getdata())
    top = Counter(px).most_common(1)[0][1]
    return len(set(px)), 1 - top / len(px)


def frame_diff(a, b):
    """两帧的平均灰度差（0~255）。"""
    fl = lambda im: list(im.get_flattened_data()) if hasattr(im, 'get_flattened_data') else list(im.getdata())
    A, B = fl(_small(a).convert('L')), fl(_small(b).convert('L'))
    return sum(abs(x - y) for x, y in zip(A, B)) / len(A)


def auto_title(c, scan=40, step=10, stable_need=3, top=6):
    """从开机开始每 step 帧采样，把“静止画面”分段记录，按下面的分数排序：
         颜色数 × 前景比例 × 停留时长（标题会一直等玩家按键，停得最久）× 早出现加成
    厂商 Logo、剧情文字颜色少或停得短，分数低。20 秒内若没有像样的画面，按一次开始键跳过开场。
    返回按分数排序的候选 [(图, 帧号, 存档), ...]，模拟器停在第 1 名的时刻。"""
    segs = []                                 # 每段：[图, 帧号, 存档, 停留帧数, 颜色, 前景]
    cur, prev, stable, pressed, waits = None, None, 0, False, 0
    after = 1.0                               # 在“像标题的画面”上按过开始后，后面多半已是游戏内容
    for i in range(scan * 60 // step):
        c.run(step)
        im = c.image().convert('RGB')
        if prev is not None and frame_diff(prev, im) < 2.5:   # 允许标志闪烁、调色板动画等小变化
            stable += 1
        else:
            stable, cur = 0, None
        prev = im
        if stable == stable_need:
            colors, content = frame_info(im)
            cur = [im, c.frames, c.save_state(), 0, colors, content, False, after]
            segs.append(cur)
        if cur is not None:
            cur[3] += step
            if cur[3] >= 900:                     # 停了 15 秒：在等按键（标题，或汉化组片头等）
                if waits >= 2:
                    break
                cur[6] = True                     # 一直在等按键：很强的“标题”信号
                if cur[4] >= 8:                   # 颜色丰富的等待画面（标题）之后的画面降分；
                    after = 0.5                   # 颜色少的（汉化组片头、说明页）之后不降
                c.press('start', 6, 30)           # 按一次开始，看看后面还有没有真正的标题
                waits += 1; cur = None; stable = 0
        best_now = max((x[4] * min(x[5], 0.6) for x in segs), default=0)
        if not pressed and c.frames > 1200 and best_now < 8:
            c.press('start', 6, 30); pressed = True
    if not segs:
        return [(c.image().convert('RGB'), c.frames, c.save_state(), 1)]

    def score(x):
        early = 1.4 if x[1] < 1500 else 1.0
        plain_bg = 1.0 if x[5] <= 0.65 else 0.45        # 标题多是“纯色背景 + 标志”，满屏场景（演示画面）降分
        waited = 1.8 if x[6] else 1.0                    # 停到需要按键才继续
        return x[4] * min(x[5], 0.6) * (min(x[3], 600) / 600) ** 0.5 * early * plain_bg * waited * x[7]

    segs.sort(key=score, reverse=True)
    picked = []
    for x in segs:                            # 去掉几乎相同的画面
        if all(frame_diff(x[0], y[0]) > 6 for y in picked):
            picked.append(x)
        if len(picked) >= top:
            break
    return [(x[0], x[1], x[2], score(x)) for x in picked]


def auto_play(c, title, rounds=12, top=6):
    """从标题想办法进入游戏，挑有代表性的游戏画面：
    - 先不按键观察 15 秒（很多游戏会播放自动演示）；
    - 再每轮按开始 / A 进入，并模拟“方向 + 攻击”操作；画面持续变化说明已进入游戏，之后不再按开始；
    - 分数 = 颜色数 × 前景比例 × 活动度，和标题太像、或者静止的菜单分数低。
    返回按分数排序的候选 [(图, 帧号, 说明), ...]。"""
    moves = [['right', 'b'], ['up', 'b'], ['left', 'a'], ['right'], ['b'], ['up', 'a'], ['down', 'b'], ['a']]
    cands = []
    prev = [c.image().convert('RGB')]

    def consider(im, tag):
        colors, content = frame_info(im)
        act = frame_diff(prev[0], im)
        prev[0] = im
        if frame_diff(title, im) < 4 or content < 0.25:
            return 0, act
        sc = colors * content * (0.3 + min(act, 20) / 20)
        cands.append((sc, im, c.frames, tag))
        return sc, act

    st = c.save_state()
    for _ in range(90):                       # 不按键：很多游戏会播放自动演示
        c.run(10); consider(c.image().convert('RGB'), '自动演示')
    c.load_state(st)
    prev[0] = c.image().convert('RGB')
    playing = False
    for r in range(rounds):
        if not playing:
            # 菜单/选人界面常要先移动光标再确认：依次试 “开始”“右+开始”“下+开始”“A”
            nav = [None, 'right', 'down', None][r % 4]
            if nav:
                c.press(nav, 6, 30)
            c.press('a' if r % 4 == 3 else 'start', 6, 40)
        acts = []
        for m in moves:
            c.run(20, m)
            _, act = consider(c.image().convert('RGB'), '实际游玩')
            acts.append(act)
        if not playing and sorted(acts)[len(acts) // 2] > 6:
            playing = True                    # 画面在持续大幅变化：已经进入游戏，不再按开始（避免暂停）
    if not cands:
        return [(c.image().convert('RGB'), c.frames, '最后一帧')]
    cands.sort(key=lambda x: x[0], reverse=True)
    picked = []
    for x in cands:
        if all(frame_diff(x[1], y[1]) > 8 for y in picked):
            picked.append(x)
        if len(picked) >= top:
            break
    return [(x[1], x[2], x[3]) for x in picked]


def candidates_sheet(titles, plays, out, font=None):
    """把标题候选、游戏画面候选各一行拼在一起，带编号，方便用 --title-pick / --play-pick 换一张。"""
    font = font or next((f for f in FONTS if os.path.exists(f)), None)
    F = ImageFont.truetype(font, 16) if font else ImageFont.load_default()
    w, h = 256, 240
    cols = max(len(titles), len(plays))
    sh = Image.new('RGB', (cols * (w + 10) + 130, 2 * (h + 34) + 10), (24, 24, 24))
    d = ImageDraw.Draw(sh)
    for row, (label, items) in enumerate((('标题候选', titles), ('游戏画面候选', plays))):
        y = 10 + row * (h + 34)
        d.text((10, y + h // 2), label, font=F, fill=(230, 210, 150))
        for i, it in enumerate(items):
            x = 120 + i * (w + 10)
            sh.paste(it[0].resize((w, h)), (x, y + 24))
            d.text((x, y), '%d  第 %d 帧' % (i + 1, it[1]), font=F, fill=(255, 255, 255) if i else (255, 200, 80))
    sh.save(out)


# ------------------------------------------------------------------ 卡片

def auto_logo_box(im, gap=6, join=10, pad=6):
    """自动找标题标志：
    1. 背景色 = 画面四边最常见的颜色；
    2. 按“连续 gap 行以上没有前景像素”把画面切成若干横条；
    3. 取“面积 × 颜色数”最大的横条当标志，与它相距不超过 join 行、且不比它宽的横条一并纳入
       （例如标志上方的厂商名）；菜单、版权行通常离得远或很窄，会被排除。"""
    w, h = im.size
    edge = [im.getpixel((x, 0)) for x in range(w)] + [im.getpixel((x, h - 1)) for x in range(w)] + \
           [im.getpixel((0, y)) for y in range(h)] + [im.getpixel((w - 1, y)) for y in range(h)]
    bg = Counter(edge).most_common(1)[0][0]
    fg = lambda p: abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 60
    rows = [[x for x in range(w) if fg(im.getpixel((x, y)))] for y in range(h)]

    bands, cur, empty = [], None, 0          # 每条：[y0, y1, 像素数, x0, x1, 颜色集合]
    for y, xs in enumerate(rows):
        if xs:
            if cur is None:
                cur = [y, y, 0, w, 0, set()]
            cur[1] = y; cur[2] += len(xs); cur[3] = min(cur[3], xs[0]); cur[4] = max(cur[4], xs[-1])
            cur[5].update(im.getpixel((x, y)) for x in xs[::3])
            empty = 0
        elif cur is not None:
            empty += 1
            if empty >= gap:
                bands.append(cur); cur = None
    if cur is not None:
        bands.append(cur)
    if not bands:
        return 0, 0, w, h

    # 标志通常颜色多、面积大；大块纯色图案（口袋、边框）颜色少，排在后面
    i = max(range(len(bands)), key=lambda k: bands[k][2] ** 0.5 * min(len(bands[k][5]), 12))
    y0, y1, _, x0, x1, _ = bands[i]
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
    for (r, g, b), n in Counter(list(im.convert('RGB').getdata()) if not hasattr(im, 'get_flattened_data') else im.get_flattened_data()).most_common(64):
        mx, mn = max(r, g, b), min(r, g, b)
        sat = (mx - mn) / mx if mx else 0
        if mx >= 90 and sat >= 0.35 and n * sat > score:
            best, score = (r, g, b), n * sat
    return best


PLATFORM_BY_EXT = {'.nes': 'FC', '.fds': 'FC', '.unf': 'FC', '.sfc': 'SFC', '.smc': 'SFC', '.md': 'MD', '.gen': 'MD',
                   '.smd': 'MD', '.gba': 'GBA', '.gb': 'GB', '.gbc': 'GBC'}


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
    ap.add_argument('--label', help='顶栏文字，默认按扩展名：FC · 汉化收藏 / SFC · 汉化收藏 …')
    ap.add_argument('--title-at', type=int, help='不填则自动找标题')
    ap.add_argument('--title-keys')
    ap.add_argument('--keys', help='不填则自动进入游戏')
    ap.add_argument('--play')
    ap.add_argument('--scan', type=int, default=40, help='自动找标题时最多观察多少秒（默认 40）')
    ap.add_argument('--title-pick', type=int, default=1, help='自动模式下改用第 N 个标题候选')
    ap.add_argument('--play-pick', type=int, default=1, help='自动模式下改用第 N 个游戏画面候选')
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
        base = os.path.splitext(a.out or a.name + '_card.png')[0].removesuffix('_card')
        title, play = capture(a.rom, a.kit, a.title_at, a.keys, a.play, a.state, a.title_keys, a.scan,
                              title_pick=a.title_pick, play_pick=a.play_pick, sheet=base + '_candidates.png')
        title.save(base + '_title.png'); play.save(base + '_play.png')
    else:
        ap.error('需要 ROM，或者同时给 --title-img 和 --play-img')

    box = tuple(int(v) for v in a.logo.split(',')) if a.logo else None
    acc = tuple(int(a.accent.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) if a.accent else None
    label = a.label or '%s · 汉化收藏' % PLATFORM_BY_EXT.get(os.path.splitext(a.rom or '')[1].lower(), 'FC')
    out = a.out or a.name + '_card.png'
    make_card(title, play, a.name, a.sub, label, box, acc, a.font).save(out)
    print('收藏卡：', out)


if __name__ == '__main__':
    main()
