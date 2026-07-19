<template>
  <div class="qq-desktop">
    <div class="qq-window">
      <div class="qq-window-inner">
        <!-- 标题栏：系统级拖动（无边框窗口） -->
        <div class="qq-titlebar" style="--wails-draggable: drag;">
          <div class="qq-titlebar-icon" style="--wails-draggable: no-drag;"></div>
          <div class="qq-titlebar-text">simui</div>
          <div class="qq-titlebar-btns" style="--wails-draggable: no-drag;">
            <button type="button" class="qq-sys-btn" title="最小化" @click.stop="onMinimise">-</button>
            <button type="button" class="qq-sys-btn" title="关闭" @click.stop="onClose">×</button>
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
              :key="platform.id"
              class="qq-platform-bar"
              :class="{ 'is-open': openPlatformId === platform.id, 'is-anim': layoutReady }"
              :style="{ top: platformTops[index] + 'px' }"
              @click="togglePlatform(platform.id)"
          >
            {{ platform.name }}
          </div>

          <div class="qq-list-middle" :class="{ 'is-anim': layoutReady }" :style="middleStyle">
            <div v-if="openPlatform" class="qq-list-scroll">
              <template v-if="openPlatform.categories.length">
                <div v-for="cat in openPlatform.categories" :key="cat.id">
                  <div
                      class="qq-category-bar"
                      :class="{ 'is-open': openCategoryIds[cat.id] }"
                      @click="toggleCategory(cat.id)"
                  >
                    <span class="qq-category-tri"></span>
                    <span class="qq-category-name">{{ cat.name }}</span>
                  </div>
                  <div v-show="openCategoryIds[cat.id]">
                    <div
                        v-for="game in cat.games"
                        :key="game.id"
                        class="qq-game-item"
                        :class="{
                        'is-active': activeGameId === game.id,
                        'is-large': avatarMode === 'large',
                      }"
                        @click="activeGameId = game.id"
                        @dblclick="noop"
                    >
                      <img class="qq-game-thumb" :src="game.thumb" :alt="game.name"/>
                      <span class="qq-game-name">{{ game.name }}</span>
                    </div>
                    <div v-if="!cat.games.length" class="qq-empty-hint">（空）</div>
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
  </div>
</template>

<script setup lang="ts">
import {computed, nextTick, onBeforeUnmount, onMounted, reactive, ref} from 'vue'
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
import {mockPlatforms} from './mockData'
import 'src/css/oicq/layout.css'

const WIN_W = 220
const WIN_H = 480
/** 平台条高度（含边框），与 CSS --qq-bar-h 保持一致 */
const BAR_H = 20

const platforms = mockPlatforms
const openPlatformId = ref<number | null>(platforms[0]?.id ?? null)
const openCategoryIds = reactive<Record<number, boolean>>(
    Object.fromEntries((platforms[0]?.categories.slice(0, 2) ?? []).map((c) => [c.id, true])),
)
const activeGameId = ref<number | null>(platforms[0]?.categories[0]?.games[0]?.id ?? null)
/** 小头像：名称在右；大头像：头像居中、昵称在下 */
const avatarMode = ref<'small' | 'large'>('small')
const pressedFooter = ref('')

const listPanelRef = ref<HTMLElement | null>(null)
const panelHeight = ref(0)
const layoutReady = ref(false)
let resizeObserver: ResizeObserver | null = null

const openIndex = computed(() =>
    openPlatformId.value == null
        ? -1
        : platforms.findIndex((p) => p.id === openPlatformId.value),
)

const openPlatform = computed(() =>
    openIndex.value >= 0 ? platforms[openIndex.value] : null,
)

/** 每个平台条的 top：展开项及之上贴顶，之下贴底 */
const platformTops = computed(() => {
  const h = panelHeight.value
  const open = openIndex.value
  const n = platforms.length
  return platforms.map((_, i) => {
    if (open < 0) return i * BAR_H
    if (i <= open) return i * BAR_H
    return Math.max(i * BAR_H, h - (n - i) * BAR_H)
  })
})

const middleStyle = computed(() => {
  const open = openIndex.value
  const n = platforms.length
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

function togglePlatform(id: number) {
  if (openPlatformId.value === id) return
  openPlatformId.value = id
}

function toggleCategory(id: number) {
  openCategoryIds[id] = !openCategoryIds[id]
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

onMounted(async () => {
  applyWindowSize()
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
