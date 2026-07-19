<!-- OICQ 查找向导：独立浮窗（表单步 → 结果步） -->
<template>
  <div
      class="qq-dlg qq-search-wizard"
      :style="{ left: pos.x + 'px', top: pos.y + 'px', width: WIDTH + 'px' }"
      @mousedown="bringFront"
      @contextmenu.stop.prevent
  >
    <div class="qq-dlg-titlebar" @mousedown="onTitleMouseDown">
      <img class="qq-dlg-titlebar-icon" src="/images/ico.png" alt="" draggable="false"/>
      <div class="qq-dlg-titlebar-text">查找游戏</div>
      <div class="qq-titlebar-btns">
        <button type="button" class="qq-sys-btn close" title="关闭" @click.stop="emit('close')"></button>
      </div>
    </div>

    <!-- 步骤 1：查询条件 -->
    <template v-if="step === 1">
      <div class="qq-dlg-body">
        <fieldset class="qq-fieldset">
          <legend>查询条件</legend>
          <div class="qq-field-grid">
            <label class="qq-field-label">平台</label>
            <select class="qq-98-select qq-field-span2" :value="platformId" @change="onPlatformChange">
              <option v-for="p in platforms" :key="p.Id" :value="p.Id">{{ p.Name }}</option>
            </select>

            <label class="qq-field-label">{{ langLabel('baseType', '类型') }}</label>
            <select class="qq-98-select" v-model="form.baseType">
              <option v-for="(opt, i) in filters.base_type" :key="'t'+i" :value="opt.value">{{ opt.label }}</option>
            </select>
            <label class="qq-field-label">{{ langLabel('baseYear', '年份') }}</label>
            <select class="qq-98-select" v-model="form.baseYear">
              <option v-for="(opt, i) in filters.base_year" :key="'y'+i" :value="opt.value">{{ opt.label }}</option>
            </select>

            <label class="qq-field-label">{{ langLabel('baseProducer', '制作商') }}</label>
            <select class="qq-98-select" v-model="form.baseProducer">
              <option v-for="(opt, i) in filters.base_producer" :key="'pr'+i" :value="opt.value">{{ opt.label }}</option>
            </select>
            <label class="qq-field-label">{{ langLabel('basePublisher', '发行商') }}</label>
            <select class="qq-98-select" v-model="form.basePublisher">
              <option v-for="(opt, i) in filters.base_publisher" :key="'pu'+i" :value="opt.value">{{ opt.label }}</option>
            </select>

            <label class="qq-field-label">{{ langLabel('baseCountry', '地区') }}</label>
            <select class="qq-98-select" v-model="form.baseCountry">
              <option v-for="(opt, i) in filters.base_country" :key="'c'+i" :value="opt.value">{{ opt.label }}</option>
            </select>
            <label class="qq-field-label">{{ langLabel('baseTranslate', '汉化') }}</label>
            <select class="qq-98-select" v-model="form.baseTranslate">
              <option v-for="(opt, i) in filters.base_translate" :key="'tr'+i" :value="opt.value">{{ opt.label }}</option>
            </select>

            <label class="qq-field-label">{{ langLabel('baseVersion', '版本') }}</label>
            <select class="qq-98-select" v-model="form.baseVersion">
              <option v-for="(opt, i) in filters.base_version" :key="'v'+i" :value="opt.value">{{ opt.label }}</option>
            </select>
            <label class="qq-field-label">{{ langLabel('rating', '评分') }}</label>
            <select class="qq-98-select" v-model="form.score">
              <option v-for="(opt, i) in filters.score" :key="'s'+i" :value="opt.value">{{ opt.label }}</option>
            </select>

            <label class="qq-field-label">{{ langLabel('complete', '通关') }}</label>
            <select class="qq-98-select" v-model="form.complete">
              <option v-for="(opt, i) in filters.complete" :key="'cm'+i" :value="opt.value">{{ opt.label }}</option>
            </select>
            <span></span>
            <span></span>

            <label class="qq-field-label">{{ langLabel('gameKeyword', '关键字') }}</label>
            <input class="qq-98-input qq-field-span2" type="text" v-model="form.keyword" @keydown.enter.prevent="goNext"/>
          </div>
        </fieldset>
      </div>
      <div class="qq-dlg-footer">
        <button type="button" class="qq-98-btn is-default" :disabled="!platformId" @click="goNext">下一步 (N) &gt;</button>
        <button type="button" class="qq-98-btn" @click="emit('close')">取消</button>
      </div>
    </template>

    <!-- 步骤 2：查询结果 -->
    <template v-else>
      <div class="qq-dlg-body">
        <div class="qq-search-result-list" ref="listRef">
          <div
              v-for="game in games"
              :key="game.id"
              class="qq-search-result-item"
              :class="{ 'is-active': activeGameId === game.id }"
              @click="activeGameId = game.id"
              @dblclick="emit('run-game', game.id)"
              @contextmenu.stop.prevent="onGameContextMenu($event, game)"
          >
            <img
                v-if="game.thumb"
                class="qq-search-result-thumb"
                :src="game.thumb"
                :alt="game.name"
                @error="onThumbError"
            />
            <span v-else class="qq-search-result-thumb qq-search-result-thumb-empty"></span>
            <span class="qq-search-result-name">{{ game.name }}</span>
          </div>
          <div v-if="!loading && !games.length" class="qq-search-empty">没有找到符合条件的游戏</div>
        </div>
        <div class="qq-search-result-meta">
          <div class="qq-search-result-status">
            {{ loading ? '正在查找…' : `找到 ${totalCount} 个游戏（第 ${page + 1}/${totalPages} 页）` }}
          </div>
          <div class="qq-search-page-btns">
            <button type="button" class="qq-98-btn" :disabled="loading || page <= 0" @click="goPage(page - 1)">上页</button>
            <button type="button" class="qq-98-btn" :disabled="loading || page >= totalPages - 1" @click="goPage(page + 1)">下页</button>
          </div>
        </div>
      </div>
      <div class="qq-dlg-footer">
        <button type="button" class="qq-98-btn" @click="goPrev">&lt; 上一步 (B)</button>
        <button type="button" class="qq-98-btn" @click="emit('close')">取消</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, reactive, ref} from 'vue'
import {GetFilter, GetGameCount, GetGameList} from 'app/wailsjs/go/controller/Controller'
import {decodeApiData, notify} from 'components/utils'
import {useGlobalStore} from 'stores/globalData'
import {storeToRefs} from 'pinia'

const THEME = 'Oicq'
const PAGE_SIZE = 100
const WIDTH = 460

interface QqPlatform {
  Id: number
  Name: string
}

interface QqGame {
  id: number
  name: string
  thumb: string
}

interface FilterOpt {
  label: string
  value: string
}

const props = defineProps<{
  platforms: QqPlatform[]
  defaultPlatformId: number | null
}>()

const emit = defineEmits<{
  close: []
  'run-game': [id: number]
  'game-contextmenu': [event: MouseEvent, game: QqGame]
}>()

const global = useGlobalStore()
const {lang} = storeToRefs(global)

const step = ref(1)
const platformId = ref<number>(0)
const filters = reactive<Record<string, FilterOpt[]>>({
  base_type: [],
  base_year: [],
  base_producer: [],
  base_publisher: [],
  base_country: [],
  base_translate: [],
  base_version: [],
  score: [],
  complete: [],
})
const form = reactive({
  baseType: '',
  baseYear: '',
  baseProducer: '',
  basePublisher: '',
  baseCountry: '',
  baseTranslate: '',
  baseVersion: '',
  score: '',
  complete: '',
  keyword: '',
})

const games = ref<QqGame[]>([])
const activeGameId = ref<number | null>(null)
const page = ref(0)
const totalCount = ref(0)
const loading = ref(false)
const listRef = ref<HTMLElement | null>(null)
let reqId = 0

const pos = reactive({x: 248, y: 36})
let dragging = false
let dragOx = 0
let dragOy = 0

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))

function langLabel(key: string, fallback: string) {
  return (lang.value as any)?.[key] || fallback
}

function emptyFilters() {
  const keys = Object.keys(filters)
  keys.forEach((k) => {
    filters[k] = [{label: langLabel(filterLangKey(k), '全部'), value: ''}]
  })
}

function filterLangKey(type: string) {
  const map: Record<string, string> = {
    base_type: 'baseType',
    base_year: 'baseYear',
    base_producer: 'baseProducer',
    base_publisher: 'basePublisher',
    base_country: 'baseCountry',
    base_translate: 'baseTranslate',
    base_version: 'baseVersion',
    score: 'rating',
    complete: 'complete',
  }
  return map[type] || type
}

function applyFilterDefaults(data: any) {
  const keys = Object.keys(filters)
  keys.forEach((k) => {
    const list = Array.isArray(data?.[k]) ? data[k] : []
    filters[k] = list.length ? list : [{label: langLabel(filterLangKey(k), '全部'), value: ''}]
  })
  form.baseType = filters.base_type[0]?.value ?? ''
  form.baseYear = filters.base_year[0]?.value ?? ''
  form.baseProducer = filters.base_producer[0]?.value ?? ''
  form.basePublisher = filters.base_publisher[0]?.value ?? ''
  form.baseCountry = filters.base_country[0]?.value ?? ''
  form.baseTranslate = filters.base_translate[0]?.value ?? ''
  form.baseVersion = filters.base_version[0]?.value ?? ''
  form.score = filters.score[0]?.value ?? ''
  form.complete = filters.complete[0]?.value ?? ''
}

async function loadFilters(pid: number) {
  if (!pid) {
    emptyFilters()
    return
  }
  try {
    const result = await GetFilter(pid)
    const resp = decodeApiData(result)
    if (resp.err) {
      notify('err', resp.err)
      emptyFilters()
      return
    }
    applyFilterDefaults(resp.data || {})
  } catch {
    emptyFilters()
  }
}

function buildReq(pageNum: number) {
  return {
    theme: THEME,
    platform: platformId.value,
    catname: '',
    catnameLike: 0,
    page: pageNum,
    simpleModel: 'simple',
    keyword: form.keyword || '',
    letter: '',
    baseType: form.baseType || '',
    basePublisher: form.basePublisher || '',
    baseYear: form.baseYear || '',
    baseCountry: form.baseCountry || '',
    baseTranslate: form.baseTranslate || '',
    baseVersion: form.baseVersion || '',
    baseProducer: form.baseProducer || '',
    score: form.score || '',
    complete: form.complete || '',
  }
}

function mapGame(item: any): QqGame {
  return {
    id: item.Id,
    name: item.Name || item.RomName || '',
    thumb: item.ThumbPic || '',
  }
}

async function loadResults(pageNum: number) {
  if (!platformId.value) return
  const id = ++reqId
  loading.value = true
  try {
    const req = JSON.stringify(buildReq(pageNum))
    const [listResult, countResult] = await Promise.all([
      GetGameList(req),
      GetGameCount(req),
    ])
    if (id !== reqId) return

    const listResp = decodeApiData(listResult)
    if (listResp.err) {
      notify('err', listResp.err)
      games.value = []
      return
    }
    games.value = (Array.isArray(listResp.data) ? listResp.data : []).map(mapGame)
    activeGameId.value = games.value[0]?.id ?? null

    const countResp = decodeApiData(countResult)
    totalCount.value = countResp.err ? games.value.length : (countResp.data || 0)
    page.value = pageNum
    if (listRef.value) listRef.value.scrollTop = 0
  } finally {
    if (id === reqId) loading.value = false
  }
}

async function goNext() {
  if (!platformId.value) return
  step.value = 2
  await loadResults(0)
}

function goPrev() {
  reqId++
  loading.value = false
  step.value = 1
  games.value = []
  activeGameId.value = null
}

function goPage(p: number) {
  if (p < 0 || p >= totalPages.value || loading.value) return
  loadResults(p)
}

function onGameContextMenu(e: MouseEvent, game: QqGame) {
  activeGameId.value = game.id
  emit('game-contextmenu', e, game)
}

function onThumbError(e: Event) {
  const img = e.target as HTMLImageElement
  if (img) img.style.visibility = 'hidden'
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

function onPlatformChange(e: Event) {
  const v = Number((e.target as HTMLSelectElement).value)
  platformId.value = Number.isFinite(v) ? v : 0
  if (step.value === 1) loadFilters(platformId.value)
}

onMounted(async () => {
  const def = props.defaultPlatformId
  if (def && props.platforms.some((p) => p.Id === def)) {
    platformId.value = def
  } else if (props.platforms.length) {
    platformId.value = props.platforms[0].Id
  }
  await loadFilters(platformId.value)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>
