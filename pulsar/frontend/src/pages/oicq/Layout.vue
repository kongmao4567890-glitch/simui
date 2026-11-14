<template>
  <div class="qq-desktop" :class="{ 'is-search-open': deskOpen }" @contextmenu.prevent>
    <div
        class="qq-window"
        :style="deskOpen ? { width: currentW + 'px', height: currentH + 'px' } : undefined"
    >
      <!-- 边框拖拽缩放（浮窗桌面打开时禁用） -->
      <template v-if="!deskOpen">
        <div
            v-for="dir in resizeDirs"
            :key="dir"
            class="qq-resize-handle"
            :class="'is-' + dir"
            style="--wails-draggable: no-drag;"
            @mousedown.stop.prevent="onResizeStart(dir, $event)"
        ></div>
      </template>
      <div class="qq-window-inner">
        <!-- 标题栏：系统级拖动（无边框窗口） -->
        <div class="qq-titlebar" style="--wails-draggable: drag;">
          <img class="qq-titlebar-icon" style="--wails-draggable: no-drag;" src="/images/ico.png" alt="" draggable="false"/>
          <div class="qq-titlebar-text">{{ config.SoftName?.Name || 'simUI' }}</div>
          <div class="qq-titlebar-btns" style="--wails-draggable: no-drag;">
            <button type="button" class="qq-sys-btn minimize" title="最小化" aria-label="Minimize" @click.stop="onMinimise"></button>
            <button type="button" class="qq-sys-btn close" title="关闭" aria-label="Close" @click.stop="onClose"></button>
          </div>
        </div>

        <!-- 视图切换：小头像 / 大头像 -->
        <div class="qq-toolbar">
          <button
              type="button"
              class="qq-tool-btn"
              :class="{ 'is-active': avatarMode === 'small' }"
              title="小头像"
              @click="setAvatarMode('small')"
          >
            <img class="qq-tool-ico" src="/images/oicq/listico_small.png" alt="" draggable="false"/>
          </button>
          <button
              type="button"
              class="qq-tool-btn"
              :class="{ 'is-active': avatarMode === 'large' }"
              title="大头像"
              @click="setAvatarMode('large')"
          >
            <img class="qq-tool-ico" src="/images/oicq/listico_big.png" alt="" draggable="false"/>
          </button>
          <button
              type="button"
              class="qq-tool-btn"
              title="展示图"
              @click="openThumbType"
          >
            <img class="qq-tool-ico" src="/images/oicq/listico_thumb.png" alt="" draggable="false"/>
          </button>
        </div>

        <!-- 好友列表：平台条绝对定位 + top 过渡，实现 QQ 式滑动；平台过多时隐藏滚动条滚动 -->
        <div class="qq-list-panel" ref="listPanelRef">
          <q-scroll-area class="qq-list-panel-scroll" :visible="false">
            <div class="qq-list-content" :style="{ height: contentHeight + 'px' }">
              <div
                  v-for="(platform, index) in platforms"
                  :key="platform.Id"
                  class="qq-platform-bar"
                  :class="{ 'is-open': openPlatformId === platform.Id, 'is-anim': layoutReady }"
                  :style="{ top: platformTops[index] + 'px' }"
                  @click="togglePlatform(platform.Id)"
              >
                {{ platform.Name }}
              </div>

              <div class="qq-list-middle" :class="{ 'is-anim': layoutReady }" :style="middleStyle">
                <div v-if="openPlatformId != null" class="qq-list-scroll" ref="listScrollRef" @scroll="onListScroll">
                  <template v-if="categories.length">
                    <div v-for="cat in categories" :key="cat.path">
                      <div
                          class="qq-category-bar"
                          :class="{ 'is-open': openCategoryPath === cat.path }"
                          @click="toggleCategory(cat)"
                      >
                        <span class="qq-category-tri"></span>
                        <span class="qq-category-name">{{ cat.name }}</span>
                      </div>
                      <div v-show="openCategoryPath === cat.path">
                        <div
                            v-for="game in games"
                            :key="game.id"
                            class="qq-game-item"
                            :class="{
                            'is-active': activeGameId === game.id,
                            'is-large': avatarMode === 'large',
                          }"
                            @click="activeGameId = game.id"
                            @dblclick="runMainGame(game.id)"
                            @contextmenu.stop.prevent="showGameCtxMenu($event, game)"
                        >
                          <img
                              v-if="game.thumb"
                              class="qq-game-thumb"
                              :src="game.thumb"
                              :alt="game.name"
                              @error="onThumbError"
                          />
                          <span class="qq-game-name">{{ game.name }}</span>
                        </div>
                        <div v-if="!games.length && !gamesLoading" class="qq-empty-hint">（空）</div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </q-scroll-area>
        </div>

        <!-- 底部功能区（仅按下效果） -->
        <div class="qq-footer">
          <div class="qq-footer-row">
            <button
                type="button"
                class="qq-footer-icon"
                title="快捷工具"
                :disabled="!shortCutList.length"
                @mousedown.prevent
                @click="showShortcutMenu"
            >
              <img src="/images/oicq/tools.png" alt="" draggable="false"/>
            </button>
            <button
                type="button"
                class="qq-footer-btn"
                :class="{ 'is-pressed': pressedFooter === 'search' }"
                @mousedown="pressedFooter = 'search'"
                @mouseup="pressedFooter = ''"
                @mouseleave="pressedFooter = ''"
                @click="openSearch"
            >
              <img class="qq-footer-btn-ico" src="/images/oicq/search.png" alt="" draggable="false"/>
              <span class="qq-footer-btn-label">查 找</span>
            </button>
          </div>
          <div class="qq-statusbar">
            <button
                type="button"
                class="qq-statusbar-btn is-out"
                title="主题"
                @click="showThemeMenu"
            >
              <img class="qq-statusbar-logo" src="/images/oicq/footer_logo.png" alt="" draggable="false"/>
            </button>
            <button type="button" class="qq-statusbar-btn is-in" @click="noop" style="cursor: default;">
              <span>{{ platformGameCount }}个游戏</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    <SearchWizard
        v-if="searchOpen"
        :platforms="platforms"
        :default-platform-id="openPlatformId"
        :main-win-w="currentW"
        @close="closeSearch"
        @run-game="runMainGame"
        @game-contextmenu="showGameCtxMenu"
    />
    <ThumbTypeWizard
        v-if="thumbTypeOpen"
        :platforms="platforms"
        :thumb-type-map="blockThumbTypeMap"
        :main-win-w="currentW"
        @close="closeThumbType"
        @save="onThumbTypeSave"
    />
    <ContextMenu/>
  </div>
</template>

<script setup lang="ts">
import {computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref} from 'vue'
import {
  Quit,
  ScreenGetAll,
  WindowCenter,
  WindowGetPosition,
  WindowGetSize,
  WindowMinimise,
  WindowSetBackgroundColour,
  WindowSetMaxSize,
  WindowSetMinSize,
  WindowSetPosition,
  WindowSetSize,
  WindowUnmaximise,
} from 'app/wailsjs/runtime/runtime'
import {
  GetGameCount,
  GetGameCountByMenu,
  GetGameList,
  GetMenuList,
  GetPlatform,
  GetShortcuts,
  GetSubGameList,
  RunGame,
  RunProgram,
  UpdateOneConfig,
  UpdatePlatformUi,
} from 'app/wailsjs/go/controller/Controller'
import {callSrv, decodeApiData, gotoTheme, notify} from 'components/utils'
import {useGlobalStore} from 'stores/globalData'
import {storeToRefs} from 'pinia'
import ContextMenu from './ContextMenu.vue'
import SearchWizard from './SearchWizard.vue'
import ThumbTypeWizard from './ThumbTypeWizard.vue'
import {closeContextMenu, openContextMenu, updateContextMenuItems, type QqCtxMenuItem} from './contextMenu'
import 'src/css/oicq/oicq.css'
import 'src/css/oicq/layout.css'

const WIN_W = 220
const WIN_H = 480
const MAX_WIN_W = 700
/** 查找浮窗宽度（与 SearchWizard 一致） */
const SEARCH_WIZARD_W = 460
/** 展示图设置浮窗宽度（与 ThumbTypeWizard 一致） */
const THUMB_WIZARD_W = 360
/** 平台条高度（含边框），与 CSS --qq-bar-h 保持一致 */
const BAR_H = 20
/** 展开平台后游戏区最小高度，避免平台过多把中间挤没 */
const MIN_MIDDLE_H = 300
const PAGE_SIZE = 100
const THEME = 'Oicq'

type ResizeDir = 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw'
const resizeDirs: ResizeDir[] = ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw']

interface QqPlatform {
  Id: number
  Name: string
}

interface QqCategory {
  path: string
  name: string
  like: number
}

interface QqGame {
  id: number
  name: string
  thumb: string
}

interface QqShortcut {
  Name: string
  Path: string
}

/** 可切换主题（不含当前 Oicq） */
const themeList = [
  {id: 'Default', label: 'Default'},
  {id: 'Playnite', label: 'Playnite'},
  {id: 'Tiny', label: 'Tiny'},
]

const global = useGlobalStore()
const {activePlatform, activeMenu, menuLike, lang, theme, config} = storeToRefs(global)

const platforms = ref<QqPlatform[]>([])
const categories = ref<QqCategory[]>([])
const games = ref<QqGame[]>([])
const openPlatformId = ref<number | null>(null)
const openCategoryPath = ref<string | null>(null)
const activeGameId = ref<number | null>(null)
/** 小头像：名称在右；大头像：头像居中、昵称在下 */
const avatarMode = ref<'small' | 'large'>('small')
const pressedFooter = ref('')
const gamesLoading = ref(false)
/** 当前展开平台的游戏总数 */
const platformGameCount = ref(0)
const shortCutList = ref<QqShortcut[]>([])
/** 查找向导浮窗 */
const searchOpen = ref(false)
/** 展示图设置浮窗 */
const thumbTypeOpen = ref(false)
/** 各平台展示图类型（写入 PlatformUi.Oicq.BlockThumbType） */
const blockThumbTypeMap = ref<Record<string, string>>({})
/** 任一浮窗打开时进入桌面布局 */
const deskOpen = computed(() => searchOpen.value || thumbTypeOpen.value)

const listPanelRef = ref<HTMLElement | null>(null)
const listScrollRef = ref<HTMLElement | null>(null)
const panelHeight = ref(0)
const layoutReady = ref(false)
/** 当前主窗尺寸（关闭查找后恢复） */
const currentW = ref(WIN_W)
const currentH = ref(WIN_H)
/** 打开查找前的主窗尺寸快照 */
let searchSavedW = WIN_W
let searchSavedH = WIN_H
let resizeObserver: ResizeObserver | null = null
let maxWinH = 1080
/** 其它主题共用窗口尺寸（离开 Oicq 时恢复） */
let sharedWindowW = 800
let sharedWindowH = 600

let resizing = false
/** mousedown 后异步取尺寸期间为 true，mouseup 可取消 */
let resizeArming = false
let resizeDir: ResizeDir = 'se'
let resizeStartSX = 0
let resizeStartSY = 0
let resizeStartW = 0
let resizeStartH = 0
let resizeStartX = 0
let resizeStartY = 0

let nextPage = 0
let pageEnd = false
let gameReqId = 0
let ctxMenuReqId = 0

const openIndex = computed(() =>
    openPlatformId.value == null
        ? -1
        : platforms.value.findIndex((p) => p.Id === openPlatformId.value),
)

/** 内容高度：可视区不够时拉高，交给外层隐藏滚动条滚动 */
const contentHeight = computed(() => {
  const h = panelHeight.value
  const n = platforms.value.length
  if (openIndex.value < 0) {
    return Math.max(h, n * BAR_H)
  }
  return Math.max(h, n * BAR_H + MIN_MIDDLE_H)
})

/** 每个平台条的 top：展开项及之上贴顶，之下贴底 */
const platformTops = computed(() => {
  const h = contentHeight.value
  const open = openIndex.value
  const n = platforms.value.length
  return platforms.value.map((_, i) => {
    if (open < 0) return i * BAR_H
    if (i <= open) return i * BAR_H
    return Math.max(i * BAR_H, h - (n - i) * BAR_H)
  })
})

const middleStyle = computed(() => {
  const open = openIndex.value
  const n = platforms.value.length
  const h = contentHeight.value
  if (open < 0) {
    return {
      top: `${n * BAR_H}px`,
      bottom: '0px',
    }
  }
  const top = (open + 1) * BAR_H
  const bottom = (n - open - 1) * BAR_H
  // 防止高度过小时上下重叠
  if (top + bottom > h) {
    return {top: `${top}px`, bottom: `${Math.max(0, h - top)}px`}
  }
  return {top: `${top}px`, bottom: `${bottom}px`}
})

function measurePanel() {
  if (!listPanelRef.value) return
  panelHeight.value = listPanelRef.value.clientHeight
  if (!layoutReady.value && panelHeight.value > 0) {
    // 下一帧再开动画，避免首屏定位时出现滑动
    requestAnimationFrame(() => {
      layoutReady.value = true
    })
  }
}

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n))
}

async function refreshMaxHeight() {
  try {
    const screens = await ScreenGetAll()
    const cur = screens.find((s) => s.isCurrent) || screens.find((s) => s.isPrimary) || screens[0]
    if (cur?.height) maxWinH = cur.height
  } catch {
    // 取屏失败时保留上次/默认值
  }
}

/** 固定尺寸（查找桌面等）：min=max 锁死 */
function lockWindowSize(w: number, h: number, bg: [number, number, number, number], center = false) {
  WindowUnmaximise()
  WindowSetMinSize(0, 0)
  WindowSetMaxSize(0, 0)
  WindowSetSize(w, h)
  WindowSetMinSize(w, h)
  WindowSetMaxSize(w, h)
  WindowSetBackgroundColour(bg[0], bg[1], bg[2], bg[3])
  if (center) WindowCenter()
}

/** 可缩放主窗：最小默认尺寸，最大宽 700 / 高不超过屏幕 */
async function applyWindowSize(center = false) {
  await refreshMaxHeight()
  const w = clamp(currentW.value, WIN_W, MAX_WIN_W)
  const h = clamp(currentH.value, WIN_H, maxWinH)
  currentW.value = w
  currentH.value = h
  WindowUnmaximise()
  // 其它主题离开时可能留下 MinSize(800,600)；必须先降到 Oicq 下限，再 SetSize，否则缩窄会被系统拒绝
  WindowSetMaxSize(0, 0)
  WindowSetMinSize(WIN_W, WIN_H)
  WindowSetSize(w, h)
  WindowSetMaxSize(MAX_WIN_W, maxWinH)
  WindowSetBackgroundColour(192, 192, 192, 255)
  if (center) WindowCenter()
  // 再确认一次：个别环境下 MinSize 切换后首次 SetSize 会落到旧尺寸
  try {
    const size = await WindowGetSize()
    if (Math.abs(size.w - w) > 2 || Math.abs(size.h - h) > 2) {
      WindowSetMinSize(WIN_W, WIN_H)
      WindowSetSize(w, h)
    }
  } catch {
    // ignore
  }
}

function applySearchDesktopSize() {
  // 桌面透明，仅露出主窗与查找浮窗；宽度随主窗放大
  const deskW = Math.max(740, currentW.value + 24 + SEARCH_WIZARD_W + 24)
  const deskH = Math.max(520, currentH.value + 24)
  lockWindowSize(deskW, deskH, [0, 0, 0, 0], true)
}

function applyThumbDesktopSize() {
  const deskW = Math.max(640, currentW.value + 24 + THUMB_WIZARD_W + 24)
  const deskH = Math.max(480, currentH.value + 24)
  lockWindowSize(deskW, deskH, [0, 0, 0, 0], true)
}

function openSearch() {
  if (searchOpen.value) return
  closeContextMenu()
  endResize()
  // 先记下主窗尺寸，关闭查找时必须还原（桌面放大不能写回 currentW/H）
  if (!deskOpen.value) {
    searchSavedW = currentW.value
    searchSavedH = currentH.value
  }
  thumbTypeOpen.value = false
  searchOpen.value = true
  applySearchDesktopSize()
}

async function closeSearch() {
  if (!searchOpen.value) return
  closeContextMenu()
  searchOpen.value = false
  if (thumbTypeOpen.value) return
  // 先还原系统窗口尺寸，再退出查找桌面布局，避免主窗被撑成桌面宽
  currentW.value = searchSavedW
  currentH.value = searchSavedH
  await applyWindowSize(false)
}

function openThumbType() {
  if (thumbTypeOpen.value) return
  closeContextMenu()
  endResize()
  if (!deskOpen.value) {
    searchSavedW = currentW.value
    searchSavedH = currentH.value
  }
  searchOpen.value = false
  thumbTypeOpen.value = true
  applyThumbDesktopSize()
}

async function closeThumbType() {
  if (!thumbTypeOpen.value) return
  closeContextMenu()
  thumbTypeOpen.value = false
  if (searchOpen.value) return
  currentW.value = searchSavedW
  currentH.value = searchSavedH
  await applyWindowSize(false)
}

async function onThumbTypeSave(map: Record<string, string>) {
  blockThumbTypeMap.value = {...map}
  await saveOicqUi()
  await closeThumbType()
  // 刷新当前列表，让展示图立即生效
  if (openPlatformId.value != null && openCategoryPath.value != null) {
    clearGames()
    await loadGames(0, true)
  }
}

async function onResizeStart(dir: ResizeDir, e: MouseEvent) {
  if (deskOpen.value || resizing || resizeArming) return
  resizeArming = true
  resizeDir = dir
  resizeStartSX = e.screenX
  resizeStartSY = e.screenY
  resizeStartW = currentW.value
  resizeStartH = currentH.value
  resizeStartX = 0
  resizeStartY = 0
  await refreshMaxHeight()
  try {
    const [size, pos] = await Promise.all([WindowGetSize(), WindowGetPosition()])
    resizeStartW = size.w
    resizeStartH = size.h
    resizeStartX = pos.x
    resizeStartY = pos.y
  } catch {
    // 沿用 currentW/H
  }
  if (!resizeArming) return
  // 拖拽期间放宽约束，由前端 clamp，避免与位置联动冲突
  WindowSetMinSize(0, 0)
  WindowSetMaxSize(0, 0)
  resizing = true
  resizeArming = false
}

function onResizeMove(e: MouseEvent) {
  if (!resizing) return
  const dx = e.screenX - resizeStartSX
  const dy = e.screenY - resizeStartSY
  let w = resizeStartW
  let h = resizeStartH
  let x = resizeStartX
  let y = resizeStartY
  const dir = resizeDir

  if (dir.includes('e')) {
    w = clamp(resizeStartW + dx, WIN_W, MAX_WIN_W)
  }
  if (dir.includes('w')) {
    w = clamp(resizeStartW - dx, WIN_W, MAX_WIN_W)
    x = resizeStartX + (resizeStartW - w)
  }
  if (dir.includes('s')) {
    h = clamp(resizeStartH + dy, WIN_H, maxWinH)
  }
  if (dir.includes('n')) {
    h = clamp(resizeStartH - dy, WIN_H, maxWinH)
    y = resizeStartY + (resizeStartH - h)
  }

  currentW.value = w
  currentH.value = h
  WindowSetSize(w, h)
  if (dir.includes('w') || dir.includes('n')) {
    WindowSetPosition(x, y)
  }
}

function endResize() {
  resizeArming = false
  if (!resizing) return
  resizing = false
  WindowSetMinSize(WIN_W, WIN_H)
  WindowSetMaxSize(MAX_WIN_W, maxWinH)
  void saveOicqWindowSize()
}

function onResizeUp() {
  endResize()
}

/** 将 Oicq 尺寸/头像模式/展示图写入 PlatformUi.Oicq */
async function saveOicqUi() {
  const w = clamp(currentW.value, WIN_W, MAX_WIN_W)
  const h = clamp(currentH.value, WIN_H, maxWinH)
  currentW.value = w
  currentH.value = h
  const data = JSON.stringify({
    AvatarMode: avatarMode.value,
    WindowWidth: w,
    WindowHeight: h,
    BlockThumbType: blockThumbTypeMap.value,
  })
  await UpdatePlatformUi(0, THEME, data)
}

/** 保存窗口尺寸（兼容原调用点） */
async function saveOicqWindowSize() {
  await saveOicqUi()
}

function setAvatarMode(mode: 'small' | 'large') {
  if (avatarMode.value === mode) return
  avatarMode.value = mode
  void saveOicqUi()
}

/** 离开 Oicq：恢复 Default/Playnite/Tiny 共用窗口尺寸 */
function restoreSharedWindowSize() {
  const w = Math.max(800, sharedWindowW || 800)
  const h = Math.max(600, sharedWindowH || 600)
  WindowUnmaximise()
  WindowSetMaxSize(0, 0)
  WindowSetMinSize(800, 600)
  WindowSetSize(w, h)
  WindowSetBackgroundColour(255, 255, 255, 255)
}

function loadSharedSizeFromConfig(conf: any) {
  const cfg = conf?.Config || conf || {}
  const sw = Number(cfg.WindowWidth) || 0
  const sh = Number(cfg.WindowHeight) || 0
  sharedWindowW = sw >= 800 ? sw : 800
  sharedWindowH = sh >= 600 ? sh : 600
}

/** 从 PlatformUi.Oicq 读取窗口尺寸、头像模式与展示图 */
async function loadOicqUi() {
  const ui = await callSrv('GetPlatformUi', 0, THEME)
  const ow = Number(ui?.WindowWidth) || 0
  const oh = Number(ui?.WindowHeight) || 0
  currentW.value = ow >= WIN_W ? ow : WIN_W
  currentH.value = oh >= WIN_H ? oh : WIN_H
  avatarMode.value = ui?.AvatarMode === 'large' ? 'large' : 'small'
  const map = ui?.BlockThumbType
  blockThumbTypeMap.value = (map && typeof map === 'object') ? {...map} : {}
}

/** 切走主题前先落盘 Oicq 尺寸，避免 reload 打断异步写入 */
async function leaveToTheme(themeId: string) {
  endResize()
  if (deskOpen.value) {
    currentW.value = searchSavedW
    currentH.value = searchSavedH
    searchOpen.value = false
    thumbTypeOpen.value = false
  }
  await saveOicqWindowSize()
  restoreSharedWindowSize()
  gotoTheme(themeId)
}

function clearGames() {
  gameReqId++
  games.value = []
  activeGameId.value = null
  nextPage = 0
  pageEnd = false
  gamesLoading.value = false
}

function mapGame(item: any): QqGame {
  return {
    id: item.Id,
    name: item.Name || item.RomName || '',
    thumb: item.ThumbPic || '',
  }
}

async function loadGames(page: number, replace: boolean) {
  if (openPlatformId.value == null || openCategoryPath.value == null) return
  if (gamesLoading.value) return
  if (!replace && pageEnd) return

  const reqId = ++gameReqId
  gamesLoading.value = true
  try {
    const cat = categories.value.find((c) => c.path === openCategoryPath.value)
    const req = {
      theme: THEME,
      platform: openPlatformId.value,
      catname: openCategoryPath.value,
      catnameLike: cat?.like ?? 0,
      page,
      simpleModel: 'simple',
      keyword: '',
      letter: '',
      baseType: '',
      basePublisher: '',
      baseYear: '',
      baseCountry: '',
      baseTranslate: '',
      baseVersion: '',
      baseProducer: '',
      score: '',
      complete: '',
    }
    const result = await GetGameList(JSON.stringify(req))
    if (reqId !== gameReqId) return

    const resp = decodeApiData(result)
    if (resp.err) {
      notify('err', resp.err)
      return
    }

    const rows = Array.isArray(resp.data) ? resp.data : []
    const mapped = rows.map(mapGame)
    if (replace) {
      games.value = mapped
      if (listScrollRef.value) {
        listScrollRef.value.scrollTop = 0
      }
    } else {
      games.value = games.value.concat(mapped)
    }

    if (rows.length === 0 || rows.length < PAGE_SIZE) {
      pageEnd = true
    }
    nextPage = page + 1
  } finally {
    if (reqId === gameReqId) {
      gamesLoading.value = false
    }
  }
}

function onListScroll(e: Event) {
  const el = e.target as HTMLElement
  if (!el || gamesLoading.value || pageEnd) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 40) {
    loadGames(nextPage, false)
  }
}

async function openCategory(cat: QqCategory) {
  clearGames()
  openCategoryPath.value = cat.path
  activeMenu.value = cat.path
  menuLike.value = cat.like
  UpdateOneConfig('Menu', JSON.stringify([cat.path, cat.like]))
  await loadGames(0, true)
}

function toggleCategory(cat: QqCategory) {
  if (openCategoryPath.value === cat.path) {
    clearGames()
    openCategoryPath.value = null
    return
  }
  openCategory(cat)
}

async function loadPlatformGameCount(platformId: number) {
  const req = {
    theme: THEME,
    platform: platformId,
    catname: '',
    catnameLike: 0,
    page: 0,
    simpleModel: 'simple',
    keyword: '',
    letter: '',
    baseType: '',
    basePublisher: '',
    baseYear: '',
    baseCountry: '',
    baseTranslate: '',
    baseVersion: '',
    baseProducer: '',
    score: '',
    complete: '',
  }
  const result = await GetGameCount(JSON.stringify(req))
  const resp = decodeApiData(result)
  if (resp.err) {
    notify('err', resp.err)
    platformGameCount.value = 0
    return
  }
  platformGameCount.value = resp.data || 0
}

async function loadMenus(platformId: number) {
  categories.value = []
  clearGames()
  openCategoryPath.value = null
  platformGameCount.value = 0

  await loadPlatformGameCount(platformId)

  const countResult = await GetGameCountByMenu(platformId)
  const countResp = decodeApiData(countResult)
  if (countResp.err) {
    notify('err', countResp.err)
    return
  }
  const romCountMap = countResp.data || {}

  const menuResult = await GetMenuList(platformId)
  const menuResp = decodeApiData(menuResult)
  if (menuResp.err) {
    notify('err', menuResp.err)
    return
  }

  const list: QqCategory[] = []
  if (romCountMap['/'] != null && romCountMap['/'] > 0) {
    list.push({
      path: '/',
      name: (lang.value as any)?.notCate || '未分类',
      like: 0,
    })
  }

  const menus = Array.isArray(menuResp.data) ? menuResp.data : []
  menus.forEach((item: any) => {
    list.push({
      path: item.Path,
      name: item.Name,
      like: 1,
    })
  })
  categories.value = list

  if (!list.length) return

  const cfgPath = activeMenu.value
  const found = list.find((c) => c.path === cfgPath)
  await openCategory(found ?? list[0])
}

async function togglePlatform(id: number) {
  if (openPlatformId.value === id) return
  openPlatformId.value = id
  activePlatform.value = id
  UpdateOneConfig('Platform', id.toString())
  await loadMenus(id)
  await nextTick()
  measurePanel()
}

function onThumbError(e: Event) {
  const img = e.target as HTMLImageElement
  if (img) {
    img.style.visibility = 'hidden'
  }
}

function runMainGame(id: number) {
  closeContextMenu()
  RunGame(id, 0).then((result: string) => {
    const resp = decodeApiData(result)
    if (resp.err) {
      notify('err', resp.err)
    }
  })
}

async function showGameCtxMenu(event: MouseEvent, game: QqGame) {
  activeGameId.value = game.id
  const reqId = ++ctxMenuReqId
  const {clientX, clientY} = event
  const runPrefix = (lang.value as any)?.run || '启动'
  const items: QqCtxMenuItem[] = [
    {
      label: runPrefix + game.name,
      onClick: () => runMainGame(game.id),
    },
  ]
  openContextMenu(clientX, clientY, items)

  try {
    const result = await GetSubGameList(game.id)
    if (reqId !== ctxMenuReqId) return
    const resp = decodeApiData(result)
    if (resp.err || !Array.isArray(resp.data) || resp.data.length === 0) return

    resp.data.forEach((item: any) => {
      items.push({
        label: runPrefix + (item.Name || ''),
        onClick: () => runMainGame(item.Id),
      })
    })
    // 菜单仍开着时刷新子游戏项
    updateContextMenuItems(items)
  } catch {
    // 子游戏加载失败时保留主游戏项
  }
}

function runShortcut(path: string) {
  closeContextMenu()
  RunProgram(path).then((result: string) => {
    const resp = decodeApiData(result)
    if (resp.err) {
      notify('err', resp.err)
    }
  })
}

function showShortcutMenu(e: MouseEvent) {
  if (!shortCutList.value.length) return
  const btn = e.currentTarget as HTMLElement
  const rect = btn.getBoundingClientRect()
  const items: QqCtxMenuItem[] = shortCutList.value.map((item) => ({
    label: item.Name || item.Path,
    onClick: () => runShortcut(item.Path),
  }))
  // 贴按钮左上角打开，由 clamp 自动上移避免超出窗口
  openContextMenu(rect.left, rect.top, items)
}

function showThemeMenu(e: MouseEvent) {
  const btn = e.currentTarget as HTMLElement
  const rect = btn.getBoundingClientRect()
  const items: QqCtxMenuItem[] = themeList.map((item) => ({
    label: item.label,
    onClick: () => {
      void leaveToTheme(item.id)
    },
  }))
  openContextMenu(rect.left, rect.top, items)
}

async function loadShortcuts() {
  const result = await GetShortcuts(true)
  const resp = decodeApiData(result)
  if (resp.err) {
    notify('err', resp.err)
    shortCutList.value = []
    return
  }
  shortCutList.value = Array.isArray(resp.data) ? resp.data : []
}

function onMinimise() {
  WindowMinimise()
}

function onClose() {
  Quit()
}

function noop() {
  // 功能预留
}

async function initData() {
  theme.value = THEME
  const conf = await callSrv('GetConfig')
  global.initData(conf)
  loadSharedSizeFromConfig(conf)
  await loadOicqUi()

  await loadShortcuts()

  const result = await GetPlatform()
  const resp = decodeApiData(result)
  if (resp.err) {
    notify('err', resp.err)
    return
  }

  platforms.value = Array.isArray(resp.data) ? resp.data : []
  if (!platforms.value.length) {
    openPlatformId.value = null
    return
  }

  let pid = Number(conf.Config.Platform)
  if (!platforms.value.some((p) => p.Id === pid)) {
    pid = platforms.value[0].Id
  }

  openPlatformId.value = pid
  activePlatform.value = pid
  if (pid !== Number(conf.Config.Platform)) {
    UpdateOneConfig('Platform', pid.toString())
  }

  await loadMenus(pid)
}

onMounted(() => {
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', onResizeUp)
})

onActivated(async () => {
  // keep-alive：每次切入 Oicq 都要用独立尺寸，不能沿用其它主题的 WindowWidth
  if (deskOpen.value) {
    currentW.value = searchSavedW
    currentH.value = searchSavedH
    searchOpen.value = false
    thumbTypeOpen.value = false
  }
  await initData()
  await applyWindowSize(true)
  await nextTick()
  measurePanel()
  if (listPanelRef.value && !resizeObserver) {
    resizeObserver = new ResizeObserver(() => measurePanel())
    resizeObserver.observe(listPanelRef.value)
  }
})

onDeactivated(() => {
  endResize()
  if (deskOpen.value) {
    // 切主题时若浮窗仍开着，先合上并回到主窗尺寸再保存
    currentW.value = searchSavedW
    currentH.value = searchSavedH
    searchOpen.value = false
    thumbTypeOpen.value = false
  }
  void saveOicqWindowSize()
  restoreSharedWindowSize()
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', onResizeUp)
  endResize()
  resizeObserver?.disconnect()
  resizeObserver = null
  if (deskOpen.value) {
    currentW.value = searchSavedW
    currentH.value = searchSavedH
    searchOpen.value = false
    thumbTypeOpen.value = false
  }
  void saveOicqWindowSize()
  restoreSharedWindowSize()
})
</script>
