<template>
  <div class="qq-desktop">
    <div class="qq-window">
      <div class="qq-window-inner">
        <!-- 标题栏：系统级拖动（无边框窗口） -->
        <div class="qq-titlebar" style="--wails-draggable: drag;">
          <div class="qq-titlebar-icon" style="--wails-draggable: no-drag;"></div>
          <div class="qq-titlebar-text">simui</div>
          <div class="qq-titlebar-btns" style="--wails-draggable: no-drag;">
            <button type="button" class="qq-sys-btn" title="最小化" @click.stop="onMinimise">_</button>
            <button type="button" class="qq-sys-btn" title="关闭" @click.stop="onClose">×</button>
          </div>
        </div>

        <!-- 工具栏占位图标 -->
        <div class="qq-toolbar">
          <button
            v-for="(ico, i) in toolbarIcons"
            :key="i"
            type="button"
            class="qq-tool-btn"
            :class="{ 'is-pressed': pressedTool === i }"
            :title="ico.title"
            @mousedown="pressedTool = i"
            @mouseup="pressedTool = -1"
            @mouseleave="pressedTool = -1"
            @click="noop"
          >{{ ico.glyph }}</button>
        </div>

        <!-- 好友列表：展开平台在上，其后的平台贴底（经典 QQ 布局） -->
        <div class="qq-list-panel">
          <div class="qq-list-top">
            <div
              v-for="platform in platformsAbove"
              :key="platform.id"
              class="qq-platform-bar"
              @click="togglePlatform(platform.id)"
            >
              {{ platform.name }}
            </div>

            <template v-if="openPlatform">
              <div
                class="qq-platform-bar is-open"
                @click="togglePlatform(openPlatform.id)"
              >
                {{ openPlatform.name }}
              </div>
            </template>

            <!-- 无展开时：全部平台堆在上方 -->
            <template v-if="!openPlatform">
              <div
                v-for="platform in platforms"
                :key="'all-' + platform.id"
                class="qq-platform-bar"
                @click="togglePlatform(platform.id)"
              >
                {{ platform.name }}
              </div>
            </template>
          </div>

          <div v-if="openPlatform" class="qq-list-middle">
            <div class="qq-list-scroll">
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
                      :class="{ 'is-active': activeGameId === game.id }"
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
          <div v-else class="qq-list-middle qq-list-middle-empty"></div>

          <div class="qq-list-bottom">
            <div
              v-for="platform in platformsBelow"
              :key="platform.id"
              class="qq-platform-bar"
              @click="togglePlatform(platform.id)"
            >
              {{ platform.name }}
            </div>
          </div>
        </div>

        <!-- 底部功能区（仅按下效果） -->
        <div class="qq-footer">
          <div class="qq-footer-row">
            <button type="button" class="qq-footer-icon" @mousedown.prevent @click="noop">🔍</button>
            <button
              type="button"
              class="qq-footer-btn"
              :class="{ 'is-pressed': pressedFooter === 'search' }"
              @mousedown="pressedFooter = 'search'"
              @mouseup="pressedFooter = ''"
              @mouseleave="pressedFooter = ''"
              @click="noop"
            >搜索</button>
          </div>
          <div class="qq-footer-row">
            <button type="button" class="qq-footer-icon" @mousedown.prevent @click="noop">▶</button>
            <button
              type="button"
              class="qq-footer-btn"
              :class="{ 'is-pressed': pressedFooter === 'launch' }"
              @mousedown="pressedFooter = 'launch'"
              @mouseup="pressedFooter = ''"
              @mouseleave="pressedFooter = ''"
              @click="noop"
            >启动</button>
          </div>
          <div class="qq-statusbar">
            <div class="qq-statusbar-left">
              <span class="qq-dot"></span>
              <span>QQ2000</span>
            </div>
            <div class="qq-statusbar-right">
              <span class="qq-dot"></span>
              <span>在线</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, reactive, ref} from 'vue'
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
import 'src/css/qq2000/layout.css'

const WIN_W = 220
const WIN_H = 480

const platforms = mockPlatforms
const openPlatformId = ref<number | null>(platforms[0]?.id ?? null)
const openCategoryIds = reactive<Record<number, boolean>>(
  Object.fromEntries((platforms[0]?.categories.slice(0, 2) ?? []).map((c) => [c.id, true])),
)
const activeGameId = ref<number | null>(platforms[0]?.categories[0]?.games[0]?.id ?? null)
const pressedTool = ref(-1)
const pressedFooter = ref('')

const openIndex = computed(() =>
  openPlatformId.value == null
    ? -1
    : platforms.findIndex((p) => p.id === openPlatformId.value),
)

const openPlatform = computed(() =>
  openIndex.value >= 0 ? platforms[openIndex.value] : null,
)

/** 展开项之上的平台（贴顶） */
const platformsAbove = computed(() =>
  openIndex.value > 0 ? platforms.slice(0, openIndex.value) : [],
)

/** 展开项之下的平台（贴底） */
const platformsBelow = computed(() =>
  openIndex.value >= 0 ? platforms.slice(openIndex.value + 1) : [],
)

const toolbarIcons = [
  {glyph: '⚓', title: '功能预留'},
  {glyph: '📁', title: '功能预留'},
  {glyph: '🌐', title: '功能预留'},
  {glyph: '📱', title: '功能预留'},
]

function applyWindowSize() {
  WindowUnmaximise()
  // 先放开限制，再锁定到 QQ 小窗尺寸
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

onMounted(() => {
  applyWindowSize()
})

onBeforeUnmount(() => {
  // 切回其他主题时恢复默认可缩放尺寸
  restoreWindowSize()
})
</script>
