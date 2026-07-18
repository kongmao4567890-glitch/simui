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

/** 占位缩略图：纯色方块 + 首字 */
function thumb(label: string, color: string): string {
  const ch = encodeURIComponent(label.slice(0, 1))
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">
    <rect width="32" height="32" fill="${color}"/>
    <text x="16" y="22" text-anchor="middle" font-size="14" font-family="SimSun,serif" fill="#fff">${ch}</text>
  </svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

export const mockPlatforms: QqPlatform[] = [
  {
    id: 1,
    name: 'FC 红白机',
    categories: [
      {
        id: 11,
        name: '动作(3/8)',
        games: [
          {id: 101, name: '超级玛丽', thumb: thumb('超', '#e74c3c')},
          {id: 102, name: '魂斗罗', thumb: thumb('魂', '#3498db')},
          {id: 103, name: '坦克大战', thumb: thumb('坦', '#27ae60')},
        ],
      },
      {
        id: 12,
        name: '角色扮演(2/5)',
        games: [
          {id: 104, name: '最终幻想', thumb: thumb('最', '#9b59b6')},
          {id: 105, name: '勇者斗恶龙', thumb: thumb('勇', '#f39c12')},
        ],
      },
      {
        id: 13,
        name: '射击(1/3)',
        games: [
          {id: 106, name: '1942', thumb: thumb('1', '#1abc9c')},
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
          {id: 201, name: '超级马里奥世界', thumb: thumb('玛', '#e67e22')},
          {id: 202, name: '星之卡比', thumb: thumb('星', '#e91e63')},
        ],
      },
      {
        id: 22,
        name: '格斗(2/4)',
        games: [
          {id: 203, name: '街头霸王2', thumb: thumb('街', '#c0392b')},
          {id: 204, name: '饿狼传说', thumb: thumb('饿', '#8e44ad')},
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
          {id: 301, name: '索尼克', thumb: thumb('索', '#2980b9')},
          {id: 302, name: '怒之铁拳', thumb: thumb('怒', '#d35400')},
          {id: 303, name: '梦幻之星', thumb: thumb('梦', '#16a085')},
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
          {id: 401, name: '拳皇97', thumb: thumb('拳', '#c0392b')},
          {id: 402, name: '三国战纪', thumb: thumb('三', '#2c3e50')},
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
