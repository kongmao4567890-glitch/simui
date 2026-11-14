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
              <q-item clickable v-close-popup @click="gotoTheme('Gallery')">
                <q-item-section>Gallery · 展馆</q-item-section>
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
import SPlatform from 'src/pages/playnite/Platform.vue'
import SContext from 'src/pages/classic/context/Context.vue'
import BookSlot from 'src/pages/book/BookSlot.vue'
import {gotoTheme} from 'components/utils'
import {useGameBrowser} from 'src/composables/useGameBrowser'

const {
  t, lang, config, platformUi, items, index, detail, pics, strategy, strategyFiles, simId, flipDir, tocOpen, tocKeyword, platformName, loadingList, pageEnd, romCount, gameName, simulators, simOptions, completeText, profileRows, formattedStrategy, deskStyle, firstPic, loadList, loadMore, searchToc, flip, gotoIndex, onWheel, changeSim, run, runProgram, viewImages, addRes, openMore, windowMaximise, windowFullscreen, createCache, about, currentFont, pauseVideos, renderPage,
  WindowMinimise, Quit, openPlatformDialog,
} = useGameBrowser('Book', '.book-root')
</script>

<style>
@import "src/css/book/book.css";
</style>
