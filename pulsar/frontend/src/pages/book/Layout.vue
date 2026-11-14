<!--
  游戏年鉴（Book）主题

  打开后直接展示“一个游戏 = 一个跨页”，像翻开一本游戏年鉴：
    左页：书眉 / 图标 + 游戏名 / 封面(包装盒) + 标题画面 + 卡带 / 资料卡 + 展示图 / 页码
    右页：书眉 / 游戏画面 + 动画 + 视频 / 海报 + 简介 / 攻略 + 图文杂志 / 开始游戏 / 页码
    桌面：背景图（没有则使用平台界面背景）
  每个素材都有固定版位；缺少素材时显示占位框，点击即可从本地添加。
-->
<template>
  <div class="border-out">
    <div class="border-in book-root" :style="{ fontFamily: currentFont }">

      <!-- 桌面背景 -->
      <div class="book-desk" :style="deskStyle"></div>
      <div class="book-desk-shade"></div>

      <!-- 顶部工具栏 -->
      <q-toolbar class="book-toolbar" style="--wails-draggable:drag;">
        <div class="book-logo" @dblclick="windowMaximise()">
          <q-icon name="auto_stories" size="18px"/>
          <span v-if="config.SoftName">{{ config.SoftName.Name }}</span>
          <span class="book-logo-sub">{{ t('bookTitle', '游戏年鉴') }}</span>
        </div>

        <q-btn flat dense no-caps icon="apps" :label="platformName || t('bookPlatform', '平台')"
               class="book-tool-btn" @click="openPlatformDialog()">
          <q-tooltip>{{ t('bookSwitchPlatform', '切换平台 / 目录') }}</q-tooltip>
        </q-btn>
        <q-btn flat dense no-caps icon="toc" :label="t('bookToc', '目录')" class="book-tool-btn"
               @click="tocOpen = !tocOpen"/>

        <q-space/>

        <q-btn flat dense round icon="chevron_left" class="book-tool-btn" :disable="index <= 0" @click="flip(-1)">
          <q-tooltip>{{ t('bookPrev', '上一页') }}</q-tooltip>
        </q-btn>
        <div class="book-pageno">
          <span class="book-pageno-name">{{ detail ? gameName : '' }}</span>
          <span>{{ items.length ? (index + 1) : 0 }} / {{ romCount }}</span>
        </div>
        <q-btn flat dense round icon="chevron_right" class="book-tool-btn"
               :disable="index < 0 || index + 1 >= romCount" @click="flip(1)">
          <q-tooltip>{{ t('bookNext', '下一页') }}</q-tooltip>
        </q-btn>

        <q-space/>

        <q-btn flat dense round icon="edit_note" class="book-tool-btn" :disable="!detail"
               @click="openMore($event)">
          <q-tooltip>{{ t('bookEdit', '编辑本页') }}</q-tooltip>
        </q-btn>
        <q-btn flat dense round icon="checkroom" class="book-tool-btn">
          <q-tooltip>{{ lang.theme }}</q-tooltip>
          <q-menu>
            <q-list dense>
              <q-item clickable v-close-popup @click="gotoTheme('Default')">
                <q-item-section>Classic</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="gotoTheme('Playnite')">
                <q-item-section>Playnite</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="gotoTheme('Tiny')">
                <q-item-section>Tiny</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="gotoTheme('Oicq')">
                <q-item-section>OICQ</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
        <q-btn flat dense round icon="menu" class="book-tool-btn">
          <q-menu>
            <q-list dense style="min-width: 160px">
              <router-link to="/config">
                <q-item clickable>
                  <q-item-section>{{ lang.systemConfig }}</q-item-section>
                </q-item>
              </router-link>
              <router-link to="/platform">
                <q-item clickable>
                  <q-item-section>{{ lang.platformConfig }}</q-item-section>
                </q-item>
              </router-link>
              <router-link to="/romManage">
                <q-item clickable>
                  <q-item-section>{{ lang.romManage }}</q-item-section>
                </q-item>
              </router-link>
              <q-separator/>
              <q-item clickable v-close-popup @click="createCache('platform')">
                <q-item-section>{{ lang.createCachePlatform }}</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="createCache('all')">
                <q-item-section>{{ lang.createCacheAll }}</q-item-section>
              </q-item>
              <q-separator/>
              <q-item clickable v-close-popup @click="about()">
                <q-item-section>{{ lang.about }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>

        <div class="book-window-ctl">
          <q-btn flat dense square icon="minimize" @mousedown="WindowMinimise()"/>
          <q-btn flat dense square icon="crop_square" @mousedown="windowMaximise()"/>
          <q-btn flat dense square icon="fullscreen" @mousedown="windowFullscreen()"/>
          <q-btn flat dense square icon="close" class="book-close" @mousedown="Quit()"/>
        </div>
      </q-toolbar>

      <!-- 跨页 -->
      <div class="book-stage">
        <transition :name="flipDir > 0 ? 'book-next' : 'book-prev'" mode="out-in">
          <div class="book-spread" :key="detail ? detail.Info.Id : 'empty'" v-if="detail"
               @contextmenu.prevent="openMore($event)" @wheel="onWheel">

            <!-- ============ 左页 ============ -->
            <section class="book-page book-left">
              <header class="book-head">
                <span>{{ t('bookTitle', '游戏年鉴') }} · {{ platformName }}</span>
                <span>{{ detail.Info.BaseYear }}</span>
              </header>

              <div class="book-titlebox">
                <book-slot type="icon" class="slot-icon" compact :pics="pics" :label="lang.icon || '图标'"
                           @add="addRes" @view="viewImages"/>
                <div class="book-name">
                  <h1 class="selectable">{{ gameName }}</h1>
                  <p>
                    <span v-if="detail.Info.BaseNameEn">{{ detail.Info.BaseNameEn }} · </span>
                    <span v-if="detail.Info.BaseNameJp">{{ detail.Info.BaseNameJp }} · </span>
                    <span>{{ detail.Info.RomName }}</span>
                  </p>
                </div>
              </div>

              <div class="book-row book-cover">
                <book-slot type="packing" class="slot-packing" :pics="pics"
                           :label="t('bookCover', '封面 · 包装盒')" @add="addRes" @view="viewImages"/>
                <div class="book-col">
                  <book-slot type="title" :pics="pics" :label="lang.title || '标题图'" @add="addRes"
                             @view="viewImages"/>
                  <book-slot type="cassette" :pics="pics" :label="lang.cassette || '卡带图'" @add="addRes"
                             @view="viewImages"/>
                </div>
              </div>

              <div class="book-section">{{ t('bookProfile', '资料卡') }}</div>
              <div class="book-row book-profile">
                <table class="book-table">
                  <tbody>
                  <tr v-for="row in profileRows" :key="row.label">
                    <th>{{ row.label }}</th>
                    <td :class="row.value ? 'selectable' : 'book-na'">{{ row.value || '—' }}</td>
                  </tr>
                  </tbody>
                </table>
                <book-slot type="thumb" class="slot-thumb" :pics="pics" :label="lang.thumb || '展示图'"
                           @add="addRes" @view="viewImages"/>
              </div>

              <footer class="book-folio">— {{ (index + 1) * 2 - 1 }} —</footer>
            </section>

            <div class="book-gutter"></div>

            <!-- ============ 右页 ============ -->
            <section class="book-page book-right">
              <header class="book-head">
                <span>{{ gameName }}</span>
                <span>{{ t('bookPage', '第') }} {{ index + 1 }} / {{ romCount }}</span>
              </header>

              <div class="book-row book-screens">
                <book-slot type="snap" class="slot-snap" :pics="pics" :label="lang.snap || '插画'" @add="addRes"
                           @view="viewImages"/>
                <div class="book-col slot-side">
                  <book-slot type="gif" :pics="pics" :label="lang.gif || '动画'" @add="addRes"
                             @view="viewImages"/>
                  <book-slot type="video" :pics="pics" :label="lang.video || '视频'" @add="addRes"
                             @view="viewImages"/>
                </div>
              </div>

              <div class="book-row book-text">
                <book-slot type="poster" class="slot-poster" :pics="pics" :label="lang.poster || '海报'"
                           @add="addRes" @view="viewImages"/>
                <div class="book-col book-doc">
                  <div class="book-section book-section-top">{{ t('bookIntro', '游戏简介') }}</div>
                  <div class="book-doc-body selectable" v-if="detail.DocContent" v-html="detail.DocContent"></div>
                  <div class="book-doc-body book-na" v-else>{{ lang.GameDocIsNotExists || t('bookNoDoc', '暂无简介') }}</div>
                </div>
              </div>

              <div class="book-section">{{ t('bookStrategy', '攻略要点') }}</div>
              <div class="book-strategy">
                <div class="book-files" v-if="strategyFiles && strategyFiles.length">
                  <span class="book-file" v-for="f in strategyFiles" :key="f.Path" @click="runProgram(f.Path)">
                    <q-icon name="description" size="14px"/> {{ f.Name }}
                  </span>
                </div>
                <div v-if="strategy" class="selectable" v-html="formattedStrategy"></div>
                <div v-else-if="!strategyFiles || !strategyFiles.length" class="book-na">
                  {{ lang.noStrategy || t('bookNoStrategy', '暂无攻略') }}
                </div>
              </div>

              <div class="book-play">
                <q-select v-if="simulators.length > 1" dense outlined square options-dense emit-value map-options
                          v-model="simId" :options="simOptions" class="book-sim" @update:model-value="changeSim"/>
                <span v-else-if="simulators.length == 1" class="book-sim-one">{{ simulators[0].Name }}</span>
                <span v-else class="book-sim-one book-na">{{ t('bookNoSim', '未配置模拟器') }}</span>
                <q-btn unelevated no-caps class="book-run" icon="play_arrow" :label="t('bookPlay', '开始游戏')"
                       @click="run(detail.Info.Id)"/>
                <q-btn unelevated no-caps class="book-run book-run-sub" v-for="sub in detail.Sublist" :key="sub.Id"
                       :label="sub.Name" @click="run(sub.Id)"/>
                <q-space/>
                <span class="book-stat">
                  <span v-if="detail.Info.Score > 0">★ {{ detail.Info.Score }}</span>
                  <span>{{ completeText }}</span>
                </span>
              </div>

              <footer class="book-folio book-folio-r">— {{ (index + 1) * 2 }} —</footer>
            </section>
          </div>

          <!-- 空页面 -->
          <div class="book-spread" key="empty" v-else>
            <section class="book-page book-left">
              <header class="book-head"><span>{{ t('bookTitle', '游戏年鉴') }}</span></header>
              <div class="book-blank">{{ loadingList ? (lang.loading || '…') : t('bookNoGame', '当前目录下没有游戏') }}</div>
            </section>
            <div class="book-gutter"></div>
            <section class="book-page book-right">
              <header class="book-head"><span>&nbsp;</span></header>
              <div class="book-blank" v-if="!loadingList">
                <p>{{ t('bookNoGameTip', '请先在平台设置中添加游戏目录并生成缓存') }}</p>
                <q-btn unelevated no-caps class="book-run" :label="lang.platformConfig || '平台设置'" to="/platform"/>
              </div>
            </section>
          </div>
        </transition>
      </div>

      <!-- 目录 -->
      <transition name="book-toc">
        <div class="book-toc" v-if="tocOpen" @click.self="tocOpen = false">
          <div class="book-toc-panel">
            <div class="book-toc-head">
              <q-icon name="toc"/>
              {{ t('bookToc', '目录') }} · {{ platformName }}
              <q-space/>
              <q-btn flat dense round icon="close" size="sm" @click="tocOpen = false"/>
            </div>
            <q-input dense outlined square clearable v-model="tocKeyword" :placeholder="lang.gameKeyword"
                     class="book-toc-search" @update:model-value="searchToc"/>
            <q-scroll-area class="book-toc-list">
              <div v-for="(item, i) in items" :key="item.Id" class="book-toc-item"
                   :class="i === index ? 'active' : ''" @click="gotoIndex(i); tocOpen = false">
                <span class="book-toc-no">{{ i + 1 }}</span>
                <span class="book-toc-name">{{ platformUi.NameType == 1 || !item.RomName ? item.Name : item.RomName }}</span>
              </div>
              <div class="book-toc-more" v-if="!pageEnd" @click="loadMore()">{{ t('bookLoadMore', '加载更多') }}</div>
            </q-scroll-area>
          </div>
        </div>
      </transition>

      <s-platform/>
      <s-context/>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import {storeToRefs} from 'pinia'
import {Dialog, debounce} from 'quasar'
import 'viewerjs/dist/viewer.css'
import {api as viewerApi} from 'v-viewer'
import {useGlobalStore} from 'src/stores/globalData'
import {callSrv, decodeApiData, getDate, gotoTheme, isEmpty, loadFont, loading, notify} from 'components/utils'
import {
  AddGameThumb,
  CreateRomCache,
  GetAllSimulator,
  GetGameCount,
  GetGameDetail,
  GetGameList,
  GetGameStrategy,
  GetGameStrategyFiles,
  GetGameThumbs,
  GetPlatformById,
  GetRomBaseAlias,
  OpenMultiFileDialog,
  RunGame,
  RunProgram,
  SetRomSimId,
  UpdateOneConfig,
} from 'app/wailsjs/go/controller/Controller'
import {
  Quit,
  WindowFullscreen,
  WindowIsFullscreen,
  WindowMinimise,
  WindowReload,
  WindowToggleMaximise,
  WindowUnfullscreen,
} from 'app/wailsjs/runtime/runtime'
import SPlatform, {initPlatform, openPlatformDialog} from 'src/pages/playnite/Platform.vue'
import SContext, {showContextMenu} from 'src/pages/classic/context/Context.vue'
import {initThemeColor} from 'src/pages/playnite/HeaderBarTool.vue'
import AboutComponent from 'components/AboutComponent.vue'
import {createGamepadController} from 'components/gamepadInput'
import BookSlot from 'src/pages/book/BookSlot.vue'

const THEME_UI = 'Default' // 年鉴主题复用经典主题的平台界面参数

const global = useGlobalStore()
const {
  lang, config, theme, platformUi, simulatorMap, activePlatform, activeMenu, menuLike, activeRom,
  romState, romCount, callbackOpts, rombaseAlias,
} = storeToRefs(global)

const currentFont = ref('')
const items: any = ref([])
const index = ref(-1)
const detail: any = ref(null)
const pics: any = ref({})
const strategy = ref('')
const strategyFiles: any = ref([])
const simId = ref(0)
const flipDir = ref(1)
const tocOpen = ref(false)
const tocKeyword = ref('')
const platformName = ref('')
const loadingList = ref(true)
const pageEnd = ref(false)
let pageNum = 0
let renderSeq = 0

// 语言：优先语言文件，缺失时使用默认中文
function t(key: string, def: string) {
  const v = (lang.value as any)[key]
  return isEmpty(v) ? def : v
}

const gameName = computed(() => {
  if (!detail.value) return ''
  const info = detail.value.Info
  return platformUi.value.NameType == 1 || isEmpty(info.RomName) ? info.Name : info.RomName
})

const simulators = computed(() => {
  if (!detail.value) return []
  return simulatorMap.value[detail.value.Info.Platform] || []
})
const simOptions = computed(() => simulators.value.map((s: any) => ({label: s.Name, value: s.Id})))

const completeText = computed(() => {
  if (!detail.value) return ''
  const c = detail.value.Info.Complete
  if (c == 1) return lang.value.passed || '已通关'
  if (c == 2) return lang.value.perfectClear || '完美通关'
  return ''
})

function alias(key: string, def: string) {
  const a = (rombaseAlias.value as any) || {}
  return isEmpty(a[key]) ? def : a[key]
}

const profileRows = computed(() => {
  if (!detail.value) return []
  const i = detail.value.Info
  const rows = [
    {label: alias('Type', lang.value.baseType || '类型'), value: i.BaseType},
    {label: alias('Year', lang.value.baseYear || '发行日期'), value: i.BaseYear},
    {label: alias('Producer', lang.value.baseProducer || '制作商'), value: i.BaseProducer},
    {label: alias('Publisher', lang.value.basePublisher || '发行商'), value: i.BasePublisher},
    {label: alias('Country', lang.value.baseCountry || '地区'), value: i.BaseCountry},
    {label: alias('Translate', lang.value.baseTranslate || '汉化组'), value: i.BaseTranslate},
    {label: alias('Version', lang.value.baseVersion || '版本'), value: i.BaseVersion},
    {label: t('bookPlatform', '平台'), value: platformName.value},
    {label: t('bookFileSize', '文件大小'), value: i.Size},
  ]
  const others = [['OtherA', i.BaseOtherA, 'baseOtherA'], ['OtherB', i.BaseOtherB, 'baseOtherB'],
    ['OtherC', i.BaseOtherC, 'baseOtherC'], ['OtherD', i.BaseOtherD, 'baseOtherD']]
  others.forEach(([k, v, lk]) => {
    if (!isEmpty(v)) rows.push({label: alias(k as string, (lang.value as any)[lk as string] || '其他信息'), value: v})
  })
  if (i.RunNum > 0) {
    rows.push({label: lang.value.runNum || '运行次数', value: String(i.RunNum)})
    rows.push({label: lang.value.lastRunTime || '最后运行', value: getDate(i.RunLasttime)})
  }
  return rows
})

const formattedStrategy = computed(() => {
  if (!strategy.value) return ''
  return strategy.value
      .replace(/\[([^\]]+)\]/g, '<div class="strategy-block-title">$1</div>')
      .replace(/(^|<br\s*\/?>)\s*--\s*(<br\s*\/?>|$)/gi, '$1<div class="strategy-block-divider"></div>$2')
})

// 桌面背景：游戏背景图 > 平台界面背景
const deskStyle = computed(() => {
  const bg = firstPic('background', true) || platformUi.value.BackgroundImage
  return bg ? {backgroundImage: 'url("' + bg + '")'} : {}
})

function firstPic(type: string, imageOnly = false) {
  const list = pics.value[type]
  if (!list || !list.length) return ''
  const p = list[0].Path
  if (imageOnly && /\.(mp4|webm|flv|avi|wmv|mkv|mov)$/i.test(p)) return ''
  return p
}

/* ---------------- 列表 ---------------- */

function listRequest(page: number) {
  return JSON.stringify({
    theme: THEME_UI,
    platform: activePlatform.value,
    catname: activeMenu.value,
    catnameLike: menuLike.value,
    baseType: '', basePublisher: '', baseYear: '', baseCountry: '', baseTranslate: '', baseVersion: '',
    baseProducer: '', score: '', complete: '',
    keyword: tocKeyword.value || '',
    page: page,
    simpleModel: 'simple',
    letter: '',
  })
}

async function loadList(keepRom = 0) {
  loadingList.value = true
  pageNum = 0
  pageEnd.value = false
  const req = listRequest(0)
  const resp = decodeApiData(await GetGameList(req))
  items.value = resp.data || []
  const cnt = decodeApiData(await GetGameCount(req))
  romCount.value = cnt.data || 0
  loadingList.value = false
  if (items.value.length >= romCount.value) pageEnd.value = true
  if (items.value.length == 0) {
    pageEnd.value = true
    index.value = -1
    detail.value = null
    pics.value = {}
    return
  }
  let i = 0
  if (keepRom > 0) {
    const found = items.value.findIndex((it: any) => it.Id == keepRom)
    if (found >= 0) i = found
  }
  gotoIndex(i)
}

async function loadMore() {
  if (pageEnd.value) return false
  const resp = decodeApiData(await GetGameList(listRequest(pageNum + 1)))
  if (!resp.data || resp.data.length == 0) {
    pageEnd.value = true
    return false
  }
  pageNum++
  items.value = items.value.concat(resp.data)
  if (items.value.length >= romCount.value) pageEnd.value = true
  return true
}

const searchToc = debounce(() => loadList(), 400)

/* ---------------- 翻页 ---------------- */

async function flip(step: number) {
  let next = index.value + step
  if (next >= items.value.length && step > 0) {
    await loadMore()
  }
  if (next < 0 || next >= items.value.length) return
  flipDir.value = step
  gotoIndex(next)
}

function gotoIndex(i: number) {
  if (i < 0 || i >= items.value.length) return
  if (i != index.value) flipDir.value = i > index.value ? 1 : -1
  index.value = i
  activeRom.value = items.value[i].Id
  renderPage(items.value[i].Id)
}

async function renderPage(id: number) {
  const seq = ++renderSeq
  const [d, th, st, sf] = await Promise.all([
    GetGameDetail(id), GetGameThumbs(id, ''), GetGameStrategy(id), GetGameStrategyFiles(id),
  ])
  if (seq != renderSeq) return // 已翻到其它页
  const dResp = decodeApiData(d)
  if (dResp.err != '') {
    notify('err', dResp.err)
    return
  }
  const grouped: any = {}
  ;(decodeApiData(th).data || []).forEach((p: any) => {
    if (!grouped[p.Type]) grouped[p.Type] = []
    grouped[p.Type].push(p)
  })
  Object.keys(grouped).forEach((k) => grouped[k].sort((a: any, b: any) => (b.Master || 0) - (a.Master || 0)))
  pics.value = grouped
  strategy.value = decodeApiData(st).data || ''
  strategyFiles.value = decodeApiData(sf).data || []
  detail.value = dResp.data

  const sims = simulatorMap.value[detail.value.Info.Platform] || []
  const cur = sims.find((s: any) => s.Id == detail.value.Info.SimId)
  simId.value = cur ? cur.Id : (sims.length ? sims[0].Id : 0)
  if (!isEmpty(detail.value.Extra?.PlatformName)) platformName.value = detail.value.Extra.PlatformName
}

function onWheel(e: WheelEvent) {
  if ((e.target as HTMLElement).closest('.book-doc-body, .book-strategy, .book-table')) return
  wheelFlip(e.deltaY > 0 ? 1 : -1)
}

const wheelFlip = debounce((step: number) => flip(step), 120, true)

/* ---------------- 游戏 ---------------- */

function changeSim(v: number) {
  if (detail.value) SetRomSimId(detail.value.Info.Id, v)
}

function run(id: number) {
  pauseVideos()
  const sid = simulators.value.length ? simId.value : 0
  RunGame(id, sid).then((result: string) => {
    const resp = decodeApiData(result)
    if (resp.err != '') notify('err', resp.err)
  })
}

function runProgram(p: string) {
  RunProgram(p).then((result: string) => {
    const resp = decodeApiData(result)
    if (resp.err != '') notify('err', resp.err)
  })
}

/* ---------------- 素材 ---------------- */

function viewImages(type: string) {
  const order = ['packing', 'title', 'cassette', 'thumb', 'snap', 'gif', 'poster', 'icon', 'background']
  const all: string[] = []
  let start = 0
  order.forEach((tp) => {
    (pics.value[tp] || []).forEach((p: any) => {
      if (/\.(mp4|webm|flv|avi|wmv|mkv|mov)$/i.test(p.Path)) return
      if (tp == type && start == 0 && all.length > 0 && !all.includes(p.Path)) start = all.length
      all.push(p.Path)
    })
  })
  if (all.length) viewerApi({images: all, options: {initialViewIndex: start}})
}

function addRes(type: string) {
  if (!detail.value) return
  OpenMultiFileDialog('media').then((result: string) => {
    const resp = decodeApiData(result)
    if (resp.err != '') {
      notify('err', resp.err)
      return
    }
    if (isEmpty(resp.data)) return
    AddGameThumb(detail.value.Info.Id, type, resp.data).then((r: string) => {
      const rr = decodeApiData(r)
      if (rr.err != '') {
        notify('err', rr.err)
        return
      }
      renderPage(detail.value.Info.Id)
    })
  })
}

// 右键 / 编辑按钮：复用经典主题的右键菜单（编辑资料、展示图、子游戏、重命名、移动、删除…）
function openMore(e: MouseEvent) {
  if (!detail.value) return
  showContextMenu(e, index.value, detail.value.Info.Id, detail.value.Info)
}

watch(callbackOpts, (v: any) => {
  if (!v || !detail.value) return
  switch (v.opt) {
    case 'romHide':
    case 'moveRomLink':
    case 'deleteRomLink':
    case 'deleteRom':
      items.value.splice(index.value, 1)
      romCount.value = Math.max(0, romCount.value - 1)
      if (items.value.length == 0) {
        detail.value = null
        index.value = -1
      } else {
        index.value = -1
        gotoIndex(Math.min(v.index, items.value.length - 1))
      }
      break
    default:
      if (v.opt == 'renameRomLink' || v.opt == 'editBaseInfo') items.value[index.value].Name = v.data
      renderPage(detail.value.Info.Id)
  }
})

// 平台 / 目录切换后重新加载
watch(romState, () => {
  tocKeyword.value = ''
  loadPlatformInfo()
  loadList()
})

function loadPlatformInfo() {
  if (activePlatform.value > 0) {
    GetPlatformById(activePlatform.value).then((r: string) => {
      const resp = decodeApiData(r)
      if (resp.err == '' && resp.data) platformName.value = resp.data.Name
    })
  } else {
    platformName.value = lang.value.all || ''
  }
  GetRomBaseAlias(activePlatform.value).then((r: string) => {
    rombaseAlias.value = decodeApiData(r).data || {}
  })
}

/* ---------------- 窗口 ---------------- */

function windowMaximise() {
  config.value.WindowState = config.value.WindowState == 1 ? 0 : 1
  UpdateOneConfig('WindowState', config.value.WindowState.toString())
  WindowToggleMaximise()
}

function windowFullscreen() {
  WindowIsFullscreen().then((full: boolean) => {
    if (full) {
      config.value.WindowState = 0
      WindowUnfullscreen()
    } else {
      config.value.WindowState = 3
      WindowFullscreen()
    }
    UpdateOneConfig('WindowState', config.value.WindowState.toString())
  })
}

function createCache(opt: string) {
  loading('show', lang.value.createCacheing)
  CreateRomCache(opt == 'all' ? 0 : activePlatform.value).then(() => WindowReload())
}

function about() {
  Dialog.create({component: AboutComponent})
}

function pauseVideos() {
  document.querySelectorAll('.book-root video').forEach((v: any) => v.pause())
}

/* ---------------- 键盘 / 手柄 ---------------- */

function isTyping(e: KeyboardEvent) {
  const el = e.target as HTMLElement
  return el.matches('input, textarea') || el.classList.contains('q-editor__content')
}

function hasDialog() {
  return document.querySelector('.q-dialog') != null || document.querySelector('.mx-context-menu') != null
}

function onKey(e: KeyboardEvent) {
  if (isTyping(e) || hasDialog()) return
  switch (e.key) {
    case 'ArrowLeft':
    case 'ArrowUp':
    case 'PageUp':
      flip(-1)
      break
    case 'ArrowRight':
    case 'ArrowDown':
    case 'PageDown':
      flip(1)
      break
    case 'Home':
      gotoIndex(0)
      break
    case 'Enter':
      if (detail.value) run(detail.value.Info.Id)
      break
    case 'Escape':
      tocOpen.value = false
      break
    case 't':
    case 'T':
      tocOpen.value = !tocOpen.value
      break
    default:
      return
  }
  e.preventDefault()
}

const pad = createGamepadController({
  handlers: {
    onNavigate: (dir: string) => {
      if (hasDialog()) return
      flip(dir == 'ArrowLeft' || dir == 'ArrowUp' ? -1 : 1)
    },
    onConfirm: () => {
      if (!hasDialog() && detail.value) run(detail.value.Info.Id)
    },
    onCancel: () => {
      tocOpen.value = false
    },
    onOpenPlatform: openPlatformDialog,
  },
  onDisconnect: () => notify('info', lang.value.gamePadDisConnect),
})

/* ---------------- 字体 ---------------- */

function initFont() {
  const ui: any = platformUi.value
  if (!ui.Font) return
  if (ui.Font.Type == 1) {
    currentFont.value = ui.Font.Family
  } else if (ui.Font.Type == 2) {
    loadFont(ui.Font.Family, ui.Font.Format, ui.Font.Src).then(() => {
      currentFont.value = ui.Font.Family
    }).catch(() => notify('err', ui.Font.Family + lang.value.fontLoadErr))
  }
}

const windowResize = debounce(() => {
  UpdateOneConfig('WindowWidth', window.innerWidth.toString())
  UpdateOneConfig('WindowHeight', window.innerHeight.toString())
}, 500)

onMounted(async () => {
  theme.value = 'Book'
  const conf = await callSrv('GetConfig')
  global.initData(conf)
  platformUi.value = (await callSrv('GetPlatformUi', conf.Config.Platform, THEME_UI)) || {}
  initFont()
  initThemeColor()
  initPlatform()

  GetAllSimulator().then((result: string) => {
    simulatorMap.value = decodeApiData(result).data || {}
  })

  loadPlatformInfo()
  await loadList()

  document.addEventListener('keydown', onKey)
  window.addEventListener('resize', windowResize)
  window.addEventListener('blur', pauseVideos)
  pad.init()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', windowResize)
  window.removeEventListener('blur', pauseVideos)
  pad.destroy()
  pauseVideos()
})
</script>

<style>
@import "src/css/book/book.css";
</style>
