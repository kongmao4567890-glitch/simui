<template>
  <div class="qq-desktop" @contextmenu.prevent>
    <div class="qq-window">
      <div class="qq-window-inner">
        <!-- 标题栏：系统级拖动（无边框窗口） -->
        <div class="qq-titlebar" style="--wails-draggable: drag;">
          <div class="qq-titlebar-icon" style="--wails-draggable: no-drag;"></div>
          <div class="qq-titlebar-text">simui</div>
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
              @click="avatarMode = 'small'"
          >
            <img class="qq-tool-ico" src="/images/oicq/listico_small.png" alt="" draggable="false"/>
          </button>
          <button
              type="button"
              class="qq-tool-btn"
              :class="{ 'is-active': avatarMode === 'large' }"
              title="大头像"
              @click="avatarMode = 'large'"
          >
            <img class="qq-tool-ico" src="/images/oicq/listico_big.png" alt="" draggable="false"/>
          </button>
        </div>

        <!-- 好友列表：平台条绝对定位 + top 过渡，实现 QQ 式滑动 -->
        <div class="qq-list-panel" ref="listPanelRef">
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
                      <span v-else class="qq-game-thumb qq-game-thumb-empty"></span>
                      <span class="qq-game-name">{{ game.name }}</span>
                    </div>
                    <div v-if="!games.length && !gamesLoading" class="qq-empty-hint">（空）</div>
                  </div>
                </div>
              </template>
              <div v-else class="qq-empty-hint">暂无分类</div>
            </div>
          </div>
        </div>

        <!-- 底部功能区（仅按下效果） -->
        <div class="qq-footer">
          <div class="qq-footer-row">
            <button type="button" class="qq-footer-icon" @mousedown.prevent @click="noop">
              <img src="/images/oicq/tools.png" alt="" draggable="false"/>
            </button>
            <button
                type="button"
                class="qq-footer-btn"
                :class="{ 'is-pressed': pressedFooter === 'search' }"
                @mousedown="pressedFooter = 'search'"
                @mouseup="pressedFooter = ''"
                @mouseleave="pressedFooter = ''"
                @click="noop"
            >
              <img class="qq-footer-btn-ico" src="/images/oicq/search.png" alt="" draggable="false"/>
              <span class="qq-footer-btn-label">查 找</span>
            </button>
          </div>
          <div class="qq-statusbar">
            <button type="button" class="qq-statusbar-btn is-out" @click="noop">
              <img class="qq-statusbar-logo" src="/images/oicq/footer_logo.png" alt="" draggable="false"/>
            </button>
            <button type="button" class="qq-statusbar-btn is-in" @click="noop">
              <span>5124个游戏</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    <ContextMenu/>
  </div>
</template>

<script setup lang="ts">
import {computed, nextTick, onBeforeUnmount, onMounted, ref} from 'vue'
import {
  Quit,
  WindowCenter,
  WindowMinimise,
  WindowSetBackgroundColour,
  WindowSetMaxSize,
  WindowSetMinSize,
  WindowSetSize,
  WindowUnmaximise,
} from 'app/wailsjs/runtime/runtime'
import {
  GetGameCountByMenu,
  GetGameList,
  GetMenuList,
  GetPlatform,
  GetSubGameList,
  RunGame,
  UpdateOneConfig,
} from 'app/wailsjs/go/controller/Controller'
import {callSrv, decodeApiData, notify} from 'components/utils'
import {useGlobalStore} from 'stores/globalData'
import {storeToRefs} from 'pinia'
import ContextMenu from './ContextMenu.vue'
import {closeContextMenu, openContextMenu, updateContextMenuItems, type QqCtxMenuItem} from './contextMenu'
import 'src/css/oicq/oicq.css'
import 'src/css/oicq/layout.css'

const WIN_W = 220
const WIN_H = 480
/** 平台条高度（含边框），与 CSS --qq-bar-h 保持一致 */
const BAR_H = 20
const PAGE_SIZE = 100
const THEME = 'Oicq'

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

const global = useGlobalStore()
const {activePlatform, activeMenu, menuLike, lang, theme} = storeToRefs(global)

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

const listPanelRef = ref<HTMLElement | null>(null)
const listScrollRef = ref<HTMLElement | null>(null)
const panelHeight = ref(0)
const layoutReady = ref(false)
let resizeObserver: ResizeObserver | null = null

let nextPage = 0
let pageEnd = false
let gameReqId = 0
let ctxMenuReqId = 0

const openIndex = computed(() =>
    openPlatformId.value == null
        ? -1
        : platforms.value.findIndex((p) => p.Id === openPlatformId.value),
)

/** 每个平台条的 top：展开项及之上贴顶，之下贴底 */
const platformTops = computed(() => {
  const h = panelHeight.value
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
  const h = panelHeight.value
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

function applyWindowSize() {
  WindowUnmaximise()
  WindowSetMinSize(0, 0)
  WindowSetMaxSize(0, 0)
  WindowSetSize(WIN_W, WIN_H)
  WindowSetMinSize(WIN_W, WIN_H)
  WindowSetMaxSize(WIN_W, WIN_H)
  WindowSetBackgroundColour(192, 192, 192, 255)
  WindowCenter()
}

function restoreWindowSize() {
  WindowSetMinSize(800, 600)
  WindowSetMaxSize(0, 0)
  WindowSetSize(800, 600)
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

async function loadMenus(platformId: number) {
  categories.value = []
  clearGames()
  openCategoryPath.value = null

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

onMounted(async () => {
  applyWindowSize()
  await initData()
  await nextTick()
  measurePanel()
  if (listPanelRef.value) {
    resizeObserver = new ResizeObserver(() => measurePanel())
    resizeObserver.observe(listPanelRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  restoreWindowSize()
})
</script>
