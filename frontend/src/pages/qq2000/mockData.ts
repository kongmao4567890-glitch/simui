export interface QqGame {
  id: number
  name: string
  thumb: string
}

export interface QqCategory {
  id: number
  name: string
  games: QqGame[]
}

export interface QqPlatform {
  id: number
  name: string
  categories: QqCategory[]
}

/** 先写死：街机 ffight 截图（Wails FileLoader 读盘） */
export const MOCK_THUMB = '/ASSET/Z2FtZXMvYXJjL3NuYXBzL2ZmaWdodC5wbmc_.asset'

export const mockPlatforms: QqPlatform[] = [
  {
    id: 1,
    name: 'FC 红白机',
    categories: [
      {
        id: 11,
        name: '动作(3/8)',
        games: [
          {id: 101, name: '超级玛丽', thumb: MOCK_THUMB},
          {id: 102, name: '魂斗罗', thumb: MOCK_THUMB},
          {id: 103, name: '坦克大战', thumb: MOCK_THUMB},
        ],
      },
      {
        id: 12,
        name: '角色扮演(2/5)',
        games: [
          {id: 104, name: '最终幻想', thumb: MOCK_THUMB},
          {id: 105, name: '勇者斗恶龙', thumb: MOCK_THUMB},
        ],
      },
      {
        id: 13,
        name: '射击(1/3)',
        games: [
          {id: 106, name: '1942', thumb: MOCK_THUMB},
        ],
      },
    ],
  },
  {
    id: 2,
    name: 'SFC 超任',
    categories: [
      {
        id: 21,
        name: '经典(2/6)',
        games: [
          {id: 201, name: '超级马里奥世界', thumb: MOCK_THUMB},
          {id: 202, name: '星之卡比', thumb: MOCK_THUMB},
        ],
      },
      {
        id: 22,
        name: '格斗(2/4)',
        games: [
          {id: 203, name: '街头霸王2', thumb: MOCK_THUMB},
          {id: 204, name: '饿狼传说', thumb: MOCK_THUMB},
        ],
      },
    ],
  },
  {
    id: 3,
    name: 'MD 世嘉',
    categories: [
      {
        id: 31,
        name: '全部(3/12)',
        games: [
          {id: 301, name: '索尼克', thumb: MOCK_THUMB},
          {id: 302, name: '怒之铁拳', thumb: MOCK_THUMB},
          {id: 303, name: '梦幻之星', thumb: MOCK_THUMB},
        ],
      },
    ],
  },
  {
    id: 4,
    name: '街机',
    categories: [
      {
        id: 41,
        name: '格斗(2/20)',
        games: [
          {id: 401, name: '拳皇97', thumb: MOCK_THUMB},
          {id: 402, name: '三国战纪', thumb: MOCK_THUMB},
        ],
      },
      {
        id: 42,
        name: '射击(0/0)',
        games: [],
      },
    ],
  },
]
