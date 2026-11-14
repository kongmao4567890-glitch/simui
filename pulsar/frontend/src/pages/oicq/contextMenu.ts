import {nextTick, reactive, ref} from 'vue'

export interface QqCtxMenuItem {
  label: string
  disabled?: boolean
  /** 该项下方显示分隔线 */
  divided?: boolean
  onClick?: () => void
}

export const ctxMenuVisible = ref(false)
export const ctxMenuItems = ref<QqCtxMenuItem[]>([])
export const ctxMenuPos = reactive({x: 0, y: 0})

let openSeq = 0
let menuEl: HTMLElement | null = null

export function setCtxMenuEl(el: HTMLElement | null) {
  menuEl = el
}

function clampPosition(clientX: number, clientY: number) {
  const pad = 2
  const w = menuEl?.offsetWidth ?? 160
  const h = menuEl?.offsetHeight ?? 80
  const maxX = Math.max(pad, window.innerWidth - w - pad)
  const maxY = Math.max(pad, window.innerHeight - h - pad)
  ctxMenuPos.x = Math.min(Math.max(pad, clientX), maxX)
  ctxMenuPos.y = Math.min(Math.max(pad, clientY), maxY)
}

/** 打开右键菜单；items 由各调用方自行组装 */
export function openContextMenu(clientX: number, clientY: number, items: QqCtxMenuItem[]) {
  const seq = ++openSeq
  ctxMenuItems.value = items
  ctxMenuVisible.value = true
  ctxMenuPos.x = clientX
  ctxMenuPos.y = clientY
  nextTick(() => {
    if (seq !== openSeq || !ctxMenuVisible.value) return
    clampPosition(clientX, clientY)
  })
}

/** 菜单仍打开时更新内容（如异步追加子游戏） */
export function updateContextMenuItems(items: QqCtxMenuItem[]) {
  if (!ctxMenuVisible.value) return
  const x = ctxMenuPos.x
  const y = ctxMenuPos.y
  ctxMenuItems.value = items
  nextTick(() => {
    if (!ctxMenuVisible.value) return
    clampPosition(x, y)
  })
}

export function closeContextMenu() {
  openSeq++
  ctxMenuVisible.value = false
  ctxMenuItems.value = []
}
