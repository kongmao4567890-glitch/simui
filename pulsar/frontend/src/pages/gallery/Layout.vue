<!--
  游戏展馆（Gallery）主题

  把每个游戏当作展馆里的一件展品：
    中央：装裱在画框里的封面（包装盒 > 海报 > 展示图 > 插画），顶灯照明
    右侧：博物馆式展品说明牌（编号、名称、年代、出品方、简介、要素、开始体验）
          + 小展柜（标题画面、插画、卡带、动画、视频）
    底部：展厅导览缩略图带，点击即可走到对应展品
    墙面：游戏背景图（模糊、压暗）
-->
<template>
  <div class="border-out">
    <div class="border-in gl-root" :style="{ fontFamily: currentFont }">
      <div class="gl-wall" :style="deskStyle"></div>
      <div class="gl-wall-shade"></div>
      <div class="gl-light"></div>

      <!-- 顶栏 -->
      <header class="gl-bar" style="--wails-draggable:drag;">
        <div class="gl-brand" @dblclick="windowMaximise()">
          <span class="gl-mark"></span>
          <span>{{ config.SoftName ? config.SoftName.Name : 'SimUI' }}</span>
          <em>{{ t('galleryTitle', '游戏展馆') }}</em>
        </div>
        <q-btn flat dense no-caps class="gl-bar-btn" icon="museum" :label="platformName || t('bookPlatform', '平台')"
               @click="openPlatformDialog()">
          <q-tooltip>{{ t('bookSwitchPlatform', '切换平台 / 目录') }}</q-tooltip>
        </q-btn>

        <q-space/>
        <div class="gl-hall" v-if="detail">
          <span>{{ t('galleryHall', '展厅') }}</span>
          <b>{{ index + 1 }}</b><i>/</i><span>{{ romCount }}</span>
        </div>
        <q-space/>

        <q-btn flat dense round icon="edit_note" class="gl-bar-btn" :disable="!detail" @click="openMore($event)">
          <q-tooltip>{{ t('bookEdit', '编辑本页') }}</q-tooltip>
        </q-btn>
        <q-btn flat dense round icon="checkroom" class="gl-bar-btn">
          <q-tooltip>{{ lang.theme }}</q-tooltip>
          <q-menu>
            <q-list dense>
              <q-item clickable v-close-popup @click="gotoTheme('Book')">
                <q-item-section>Book · 年鉴</q-item-section>
              </q-item>
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
        <q-btn flat dense round icon="menu" class="gl-bar-btn">
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
        <div class="gl-window">
          <q-btn flat dense square icon="minimize" @mousedown="WindowMinimise()"/>
          <q-btn flat dense square icon="crop_square" @mousedown="windowMaximise()"/>
          <q-btn flat dense square icon="fullscreen" @mousedown="windowFullscreen()"/>
          <q-btn flat dense square icon="close" class="gl-close" @mousedown="Quit()"/>
        </div>
      </header>

      <!-- 展厅 -->
      <main class="gl-stage" @wheel="onWheel" @contextmenu.prevent="openMore($event)">
        <button class="gl-nav gl-nav-prev" :disabled="index <= 0" @click="flip(-1)">
          <q-icon name="west" size="20px"/>
        </button>
        <button class="gl-nav gl-nav-next" :disabled="index < 0 || index + 1 >= romCount" @click="flip(1)">
          <q-icon name="east" size="20px"/>
        </button>

        <transition :name="flipDir > 0 ? 'gl-next' : 'gl-prev'" mode="out-in">
          <div class="gl-exhibit" v-if="detail" :key="detail.Info.Id">

            <!-- 主展品：画框 -->
            <section class="gl-art">
              <div class="gl-frame" :class="hero.portrait ? 'portrait' : 'landscape'">
                <div class="gl-mat">
                  <img v-if="hero.src" :src="hero.src" class="gl-art-img" @click="viewImages(hero.type)"
                       @load="onHeroLoad"/>
                  <div v-else class="gl-art-empty" @click="addRes('packing')">
                    <q-icon name="add_photo_alternate" size="34px"/>
                    <span>{{ t('galleryAddCover', '为展品添加封面') }}</span>
                  </div>
                </div>
              </div>
              <div class="gl-plinth"></div>
              <div class="gl-caption">{{ hero.label }}</div>
            </section>

            <!-- 说明牌 + 展柜 -->
            <aside class="gl-side">
              <div class="gl-placard">
                <div class="gl-no">
                  <span>{{ t('galleryExhibit', '展品') }} No.{{ pad3(index + 1) }}</span>
                  <span v-if="detail.Info.Score > 0" class="gl-score">★ {{ detail.Info.Score }}</span>
                </div>
                <h1 class="selectable">{{ gameName }}</h1>
                <p class="gl-alt" v-if="altName">{{ altName }}</p>
                <p class="gl-meta">{{ metaLine }}</p>
                <div class="gl-rule"></div>

                <div class="gl-desc selectable" v-if="detail.DocContent" v-html="detail.DocContent"></div>
                <div class="gl-desc gl-muted" v-else>{{ lang.GameDocIsNotExists || t('bookNoDoc', '暂无简介') }}</div>

                <dl class="gl-facts">
                  <template v-for="f in facts" :key="f.label">
                    <dt>{{ f.label }}</dt>
                    <dd :class="f.value ? '' : 'gl-muted'">{{ f.value || '—' }}</dd>
                  </template>
                </dl>

                <div class="gl-actions">
                  <q-btn unelevated no-caps class="gl-play" icon="play_arrow"
                         :label="t('galleryPlay', '开始体验')" @click="run(detail.Info.Id)"/>
                  <q-select v-if="simulators.length > 1" dense borderless options-dense emit-value map-options
                            v-model="simId" :options="simOptions" class="gl-sim" @update:model-value="changeSim"/>
                  <span v-else-if="simulators.length == 1" class="gl-sim-one">{{ simulators[0].Name }}</span>
                  <span v-else class="gl-sim-one gl-muted">{{ t('bookNoSim', '未配置模拟器') }}</span>
                </div>
                <div class="gl-subs" v-if="detail.Sublist && detail.Sublist.length">
                  <span v-for="sub in detail.Sublist" :key="sub.Id" class="gl-sub" @click="run(sub.Id)">
                    ▸ {{ sub.Name }}
                  </span>
                </div>
              </div>

              <div class="gl-vitrine">
                <div class="gl-vitrine-title">
                  <span>{{ t('galleryVitrine', '展柜') }}</span>
                  <span class="gl-files" v-if="strategyFiles && strategyFiles.length">
                    <span v-for="f in strategyFiles" :key="f.Path" class="gl-file" @click="runProgram(f.Path)">
                      <q-icon name="menu_book" size="13px"/> {{ f.Name }}
                    </span>
                  </span>
                </div>
                <div class="gl-vitrine-row">
                  <div v-for="v in vitrine" :key="v.type" class="gl-case" :class="v.src ? 'has' : 'empty'"
                       @click="v.src ? (v.video ? null : viewImages(v.type)) : addRes(v.type)">
                    <video v-if="v.src && v.video" :src="v.src" autoplay loop muted playsinline></video>
                    <div v-else-if="v.src" class="gl-case-img" :style="{ backgroundImage: 'url(&quot;' + v.src + '&quot;)' }"></div>
                    <q-icon v-else name="add" size="18px"/>
                    <span class="gl-case-label">{{ v.label }}</span>
                  </div>
                </div>
              </div>
            </aside>
          </div>

          <div class="gl-empty" v-else key="empty">
            <div class="gl-frame landscape">
              <div class="gl-mat gl-mat-empty">
                <q-icon name="museum" size="48px"/>
              </div>
            </div>
            <h2>{{ loadingList ? (lang.loading || '…') : t('galleryEmpty', '这个展厅还没有展品') }}</h2>
            <p v-if="!loadingList">{{ t('bookNoGameTip', '请先在平台设置中添加游戏目录并生成缓存') }}</p>
            <q-btn v-if="!loadingList" unelevated no-caps class="gl-play" :label="lang.platformConfig || '平台设置'"
                   to="/platform"/>
          </div>
        </transition>
      </main>

      <!-- 展厅导览 -->
      <footer class="gl-guide">
        <div class="gl-guide-label">{{ t('galleryGuide', '展厅导览') }}</div>
        <div class="gl-strip" ref="stripRef" @wheel.prevent="stripWheel">
          <div v-for="(it, i) in items" :key="it.Id" class="gl-thumb" :class="i === index ? 'active' : ''"
               :data-i="i" @click="gotoIndex(i)">
            <img v-if="it.ThumbPic" :src="it.ThumbPic" loading="lazy"/>
            <span v-else class="gl-thumb-text">{{ shortName(it) }}</span>
            <q-tooltip anchor="top middle" self="bottom middle" :offset="[0, 6]">{{ it.Name }}</q-tooltip>
          </div>
          <div v-if="!pageEnd" class="gl-thumb gl-more" @click="loadMore()">
            <q-icon name="more_horiz"/>
          </div>
        </div>
      </footer>

      <s-platform/>
      <s-context/>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, nextTick, ref, watch} from 'vue'
import SPlatform from 'src/pages/playnite/Platform.vue'
import SContext from 'src/pages/classic/context/Context.vue'
import {gotoTheme, isEmpty} from 'components/utils'
import {useGameBrowser} from 'src/composables/useGameBrowser'

const {
  t, lang, config, platformUi, items, index, detail, strategyFiles, simId, flipDir,
  platformName, loadingList, pageEnd, romCount, gameName, simulators, simOptions,
  deskStyle, firstPic, loadMore, flip, gotoIndex, onWheel, changeSim, run, runProgram, viewImages, addRes,
  openMore, windowMaximise, windowFullscreen, createCache, about, currentFont,
  WindowMinimise, Quit, openPlatformDialog,
} = useGameBrowser('Gallery', '.gl-root')

const stripRef = ref<HTMLElement | null>(null)
const heroRatio = ref(0.75)

const isVideo = (p: string) => /\.(mp4|webm|flv|avi|wmv|mkv|mov)$/i.test(p)

// 主展品：包装盒 > 海报 > 展示图 > 插画 > 标题画面
const hero = computed(() => {
  const order: [string, string][] = [
    ['packing', t('bookCover', '封面 · 包装盒')],
    ['poster', lang.value.poster || '海报'],
    ['thumb', lang.value.thumb || '展示图'],
    ['snap', lang.value.snap || '插画'],
    ['title', lang.value.title || '标题图'],
  ]
  for (const [type, label] of order) {
    const src = firstPic(type, true)
    if (src) return {type, label, src, portrait: heroRatio.value < 1}
  }
  return {type: 'packing', label: '', src: '', portrait: true}
})

function onHeroLoad(e: Event) {
  const img = e.target as HTMLImageElement
  if (img.naturalWidth && img.naturalHeight) heroRatio.value = img.naturalWidth / img.naturalHeight
}

// 小展柜：不重复主展品
const vitrine = computed(() => {
  const list = [
    ['title', lang.value.title || '标题图'],
    ['snap', lang.value.snap || '插画'],
    ['cassette', lang.value.cassette || '卡带图'],
    ['gif', lang.value.gif || '动画'],
    ['video', lang.value.video || '视频'],
    ['poster', lang.value.poster || '海报'],
  ]
  return list
      .filter(([type]) => type != hero.value.type)
      .slice(0, 5)
      .map(([type, label]) => {
        const src = firstPic(type)
        return {type, label, src, video: !!src && (type == 'video' || isVideo(src))}
      })
})

const altName = computed(() => {
  if (!detail.value) return ''
  const i = detail.value.Info
  return i.BaseNameEn || i.BaseNameJp || (platformUi.value.NameType == 1 && i.RomName != i.Name ? i.RomName : '')
})

const metaLine = computed(() => {
  if (!detail.value) return ''
  const i = detail.value.Info
  return [i.BaseYear, i.BaseProducer || i.BasePublisher, i.BaseCountry].filter((v) => !isEmpty(v)).join(' · ')
      || platformName.value
})

const facts = computed(() => {
  if (!detail.value) return []
  const i = detail.value.Info
  const rows = [
    {label: lang.value.baseType || '类型', value: i.BaseType},
    {label: t('bookPlatform', '平台'), value: platformName.value},
    {label: lang.value.basePublisher || '发行商', value: i.BasePublisher},
    {label: lang.value.baseTranslate || '汉化组', value: i.BaseTranslate},
    {label: lang.value.baseVersion || '版本', value: i.BaseVersion},
  ]
  if (i.RunNum > 0) rows.push({label: lang.value.runNum || '运行次数', value: String(i.RunNum)})
  return rows
})

function pad3(n: number) {
  return String(n).padStart(3, '0')
}

function shortName(it: any) {
  return (it.Name || it.RomName || '').slice(0, 4)
}

function stripWheel(e: WheelEvent) {
  if (stripRef.value) stripRef.value.scrollLeft += e.deltaY + e.deltaX
}

// 当前展品滚动到导览中央
watch(index, async (i) => {
  heroRatio.value = 0.75
  await nextTick()
  const el = stripRef.value?.querySelector(`[data-i="${i}"]`) as HTMLElement | null
  el?.scrollIntoView({behavior: 'smooth', inline: 'center', block: 'nearest'})
})

</script>

<style>
@import "src/css/gallery/gallery.css";
</style>
