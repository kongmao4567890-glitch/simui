/**
 * 单游戏浏览主题（年鉴 Book、展馆 Gallery 等）共用的数据与操作：
 * 游戏列表分页、翻页、读取详情/素材/攻略、运行游戏、添加素材、右键编辑、
 * 平台切换、键盘与手柄、窗口控制。
 *
 * themeName   写入全局 theme 的主题名
 * rootSelector 主题根节点选择器（用于暂停页面内视频）
 */
import {computed, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import {storeToRefs} from 'pinia'
import {Dialog, debounce} from 'quasar'
import 'viewerjs/dist/viewer.css'
import {api as viewerApi} from 'v-viewer'
import {useGlobalStore} from 'src/stores/globalData'
import {callSrv, decodeApiData, getDate, isEmpty, loadFont, loading, notify} from 'components/utils'
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
import {initPlatform, openPlatformDialog} from 'src/pages/playnite/Platform.vue'
import {showContextMenu} from 'src/pages/classic/context/Context.vue'
import {initThemeColor} from 'src/pages/playnite/HeaderBarTool.vue'
import AboutComponent from 'components/AboutComponent.vue'
import {createGamepadController} from 'components/gamepadInput'


const THEME_UI = 'Default' // 单游戏类主题复用经典主题的平台界面参数

export function useGameBrowser(themeName: string, rootSelector: string) {

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
    document.querySelectorAll(rootSelector + ' video').forEach((v: any) => v.pause())
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
    theme.value = themeName
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

  return {
    t,
    lang,
    config,
    platformUi,
    items,
    index,
    detail,
    pics,
    strategy,
    strategyFiles,
    simId,
    flipDir,
    tocOpen,
    tocKeyword,
    platformName,
    loadingList,
    pageEnd,
    romCount,
    gameName,
    simulators,
    simOptions,
    completeText,
    profileRows,
    formattedStrategy,
    deskStyle,
    firstPic,
    loadList,
    loadMore,
    searchToc,
    flip,
    gotoIndex,
    onWheel,
    changeSim,
    run,
    runProgram,
    viewImages,
    addRes,
    openMore,
    windowMaximise,
    windowFullscreen,
    createCache,
    about,
    currentFont,
    pauseVideos,
    renderPage,
    WindowMinimise,
    Quit,
    openPlatformDialog,
  }
}
