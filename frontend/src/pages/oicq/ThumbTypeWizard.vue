<!-- OICQ 展示图类型设置：按平台选择列表缩略图类型 -->
<template>
  <div
      class="qq-dlg qq-thumb-wizard"
      :style="{ left: pos.x + 'px', top: pos.y + 'px', width: WIDTH + 'px' }"
      @mousedown="bringFront"
      @contextmenu.stop.prevent
  >
    <div class="qq-dlg-titlebar" @mousedown="onTitleMouseDown">
      <img class="qq-dlg-titlebar-icon" src="/images/ico.png" alt="" draggable="false"/>
      <div class="qq-dlg-titlebar-text">展示图设置</div>
      <div class="qq-titlebar-btns">
        <button type="button" class="qq-sys-btn close" title="关闭" @click.stop="emit('close')"></button>
      </div>
    </div>

    <div class="qq-dlg-body">
      <fieldset class="qq-fieldset">
        <legend>平台展示图</legend>
        <div class="qq-thumb-table-wrap">
          <table class="qq-thumb-table">
            <thead>
            <tr>
              <th class="col-name">平台</th>
              <th class="col-type">展示图</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="p in platforms" :key="p.Id">
              <td class="col-name" :title="p.Name">{{ p.Name }}</td>
              <td class="col-type">
                <select class="qq-98-select" v-model="draft[String(p.Id)]">
                  <option v-for="opt in thumbOpts" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </td>
            </tr>
            <tr v-if="!platforms.length">
              <td colspan="2" class="qq-thumb-empty">暂无平台</td>
            </tr>
            </tbody>
          </table>
        </div>
      </fieldset>
    </div>

    <div class="qq-dlg-footer">
      <button type="button" class="qq-98-btn is-default" @click="onOk">确定</button>
      <button type="button" class="qq-98-btn" @click="emit('close')">取消</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, reactive} from 'vue'
import {useGlobalStore} from 'stores/globalData'
import {storeToRefs} from 'pinia'

const WIDTH = 360
const DEFAULT_THUMB = 'icon'

interface QqPlatform {
  Id: number
  Name: string
}

const props = defineProps<{
  platforms: QqPlatform[]
  /** 已保存的平台展示图 map，key 为平台 Id 字符串 */
  thumbTypeMap: Record<string, string>
  mainWinW?: number
}>()

const emit = defineEmits<{
  close: []
  save: [map: Record<string, string>]
}>()

const global = useGlobalStore()
const {lang} = storeToRefs(global)

const thumbOpts = computed(() => {
  const l = lang.value as any
  return [
    {label: l?.thumb || '缩略图', value: 'thumb'},
    {label: l?.snap || '插画', value: 'snap'},
    {label: l?.poster || '海报', value: 'poster'},
    {label: l?.packing || '包装盒', value: 'packing'},
    {label: l?.title || '标题图', value: 'title'},
    {label: l?.cassette || '卡带图', value: 'cassette'},
    {label: l?.icon || '图标', value: 'icon'},
    {label: l?.gif || '动画', value: 'gif'},
    {label: l?.background || '背景图', value: 'background'},
  ]
})

const draft = reactive<Record<string, string>>({})

const pos = reactive({x: Math.max(248, (props.mainWinW ?? 220) + 28), y: 36})
let dragging = false
let dragOx = 0
let dragOy = 0

function initDraft() {
  const src = props.thumbTypeMap || {}
  props.platforms.forEach((p) => {
    const key = String(p.Id)
    draft[key] = src[key] || DEFAULT_THUMB
  })
}

function onOk() {
  const map: Record<string, string> = {}
  props.platforms.forEach((p) => {
    const key = String(p.Id)
    map[key] = draft[key] || DEFAULT_THUMB
  })
  emit('save', map)
}

function bringFront() {
  // 占位：后续若有多浮窗可调 z-index
}

function onTitleMouseDown(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('.qq-titlebar-btns')) return
  dragging = true
  dragOx = e.clientX - pos.x
  dragOy = e.clientY - pos.y
  e.preventDefault()
}

function onMouseMove(e: MouseEvent) {
  if (!dragging) return
  const maxX = Math.max(0, window.innerWidth - WIDTH)
  const maxY = Math.max(0, window.innerHeight - 80)
  pos.x = Math.min(Math.max(0, e.clientX - dragOx), maxX)
  pos.y = Math.min(Math.max(0, e.clientY - dragOy), maxY)
}

function onMouseUp() {
  dragging = false
}

onMounted(() => {
  initDraft()
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>
