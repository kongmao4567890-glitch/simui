<!-- Win98 风格右键菜单壳：样式统一，内容由 openContextMenu(items) 传入 -->
<template>
  <Teleport to="body">
    <div
        v-if="ctxMenuVisible"
        ref="menuRef"
        class="qq-ctx-menu"
        :style="{ left: ctxMenuPos.x + 'px', top: ctxMenuPos.y + 'px' }"
        @mousedown.stop
        @contextmenu.prevent
    >
      <button
          v-for="(item, index) in ctxMenuItems"
          :key="index"
          type="button"
          class="qq-ctx-item"
          :class="{ 'is-disabled': item.disabled, 'has-divider': item.divided }"
          :disabled="item.disabled"
          @click="onSelect(item)"
      >
        <span class="qq-ctx-item-label">{{ item.label }}</span>
      </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import {onBeforeUnmount, onMounted, ref, watch} from 'vue'
import {
  closeContextMenu,
  ctxMenuItems,
  ctxMenuPos,
  ctxMenuVisible,
  setCtxMenuEl,
  type QqCtxMenuItem,
} from './contextMenu'

const menuRef = ref<HTMLElement | null>(null)

watch(menuRef, (el) => setCtxMenuEl(el), {immediate: true})

function onSelect(item: QqCtxMenuItem) {
  if (item.disabled) return
  closeContextMenu()
  item.onClick?.()
}

function onDocPointerDown(e: MouseEvent) {
  if (!ctxMenuVisible.value) return
  const el = menuRef.value
  if (el && el.contains(e.target as Node)) return
  closeContextMenu()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeContextMenu()
}

onMounted(() => {
  document.addEventListener('mousedown', onDocPointerDown, true)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('blur', closeContextMenu)
  window.addEventListener('resize', closeContextMenu)
  window.addEventListener('scroll', closeContextMenu, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocPointerDown, true)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('blur', closeContextMenu)
  window.removeEventListener('resize', closeContextMenu)
  window.removeEventListener('scroll', closeContextMenu, true)
  setCtxMenuEl(null)
})
</script>
