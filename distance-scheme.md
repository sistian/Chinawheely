# 纯前端智能距离估算方案 — Chinawheely

## 设计目标

- 无需后端服务器
- 无需地图 API 密钥或备案
- 全球客户均可使用（不受网络墙限制）
- 自动实时计算，无需人工确认
- 覆盖 80%+ 常见酒店和区域

---

## 核心思路：关键词区域匹配

为每个城市建立**预置区域距离映射表**，根据用户输入的酒店/地址关键词，自动匹配距离范围。

### 匹配优先级

1. **精确匹配** → 关键词完全匹配（如"Park Hyatt Shanghai"）
2. **区域匹配** → 包含区域名（如"The Bund"、"Pudong"、"Lujiazui"）
3. **地标匹配** → 包含知名地标（如"Forbidden City"、"Great Wall"）
4. **回退默认** → 都不匹配，使用机场默认距离

---

## 数据结构示例

```javascript
const cityZones = {
  shanghai: {
    airports: { PVG: 45, SHA: 15 },
    zones: {
      // 精确酒店匹配（优先级最高）
      'park hyatt': { dist: 2, zone: 'Lujiazui', airport: 'SHA' },
      'the peninsula': { dist: 2, zone: 'The Bund', airport: 'SHA' },
      'fairmont peace': { dist: 2, zone: 'Nanjing Road', airport: 'SHA' },
      'waldorf astoria': { dist: 2, zone: 'The Bund', airport: 'SHA' },
      'jumeirah': { dist: 2, zone: 'Lujiazui', airport: 'SHA' },
      'ritz carlton': { dist: 2, zone: 'Pudong', airport: 'SHA' },
      'four seasons': { dist: 3, zone: 'Jing\'an', airport: 'SHA' },
      'mandarin oriental': { dist: 3, zone: 'Pudong', airport: 'SHA' },
      'hyatt on the bund': { dist: 3, zone: 'The Bund', airport: 'SHA' },
      'intercontinental': { dist: 3, zone: 'Nanjing Road', airport: 'SHA' },
      'grand hyatt': { dist: 3, zone: 'Jing\'an', airport: 'SHA' },
      'shangri-la': { dist: 4, zone: 'Pudong', airport: 'SHA' },
      'pullman': { dist: 4, zone: 'Jing\'an', airport: 'SHA' },
      'marriott': { dist: 4, zone: 'Pudong', airport: 'SHA' },
      'hilton': { dist: 4, zone: 'Hongqiao', airport: 'SHA' },
      'sheraton': { dist: 5, zone: 'Hongkou', airport: 'SHA' },
      'westin': { dist: 4, zone: 'The Bund', airport: 'SHA' },
      'conrad': { dist: 4, zone: 'Lujiazui', airport: 'SHA' },
      'edition': { dist: 3, zone: 'Nanjing Road', airport: 'SHA' },
      'w hotel': { dist: 3, zone: 'The Bund', airport: 'SHA' },
      'andaz': { dist: 3, zone: 'Xintiandi', airport: 'SHA' },
      'banyan tree': { dist: 5, zone: 'Minhang', airport: 'SHA' },
      'st regis': { dist: 3, zone: 'Jing\'an', airport: 'SHA' },
      'rosewood': { dist: 3, zone: 'Jing\'an', airport: 'SHA' },
      // 区域名匹配（优先级中等）
      'bund': { dist: 2, zone: 'The Bund', airport: 'SHA' },
      'lujiazui': { dist: 2, zone: 'Lujiazui', airport: 'SHA' },
      'nanjing road': { dist: 2, zone: 'Nanjing Road', airport: 'SHA' },
      'xintiandi': { dist: 3, zone: 'Xintiandi', airport: 'SHA' },
      'french concession': { dist: 4, zone: 'Former French Concession', airport: 'SHA' },
      'jing\'an': { dist: 3, zone: 'Jing\'an', airport: 'SHA' },
      'pudong': { dist: 8, zone: 'Pudong', airport: 'SHA' },
      'hongqiao': { dist: 3, zone: 'Hongqiao', airport: 'SHA' },
      'people\'s square': { dist: 2, zone: 'People\'s Square', airport: 'SHA' },
      'huangpu': { dist: 2, zone: 'Huangpu', airport: 'SHA' },
      'changning': { dist: 5, zone: 'Changning', airport: 'SHA' },
      'xuhui': { dist: 4, zone: 'Xuhui', airport: 'SHA' },
      'yangpu': { dist: 6, zone: 'Yangpu', airport: 'SHA' },
      'minhang': { dist: 10, zone: 'Minhang', airport: 'SHA' },
      'jiading': { dist: 15, zone: 'Jiading', airport: 'SHA' },
      'songjiang': { dist: 25, zone: 'Songjiang', airport: 'SHA' },
      'qingpu': { dist: 20, zone: 'Qingpu', airport: 'SHA' },
      'baoshan': { dist: 12, zone: 'Baoshan', airport: 'SHA' },
      'fengxian': { dist: 30, zone: 'Fengxian', airport: 'SHA' },
      // 默认回退
      'default': { dist: 25, zone: 'City Center', airport: 'SHA' }
    }
  },
  beijing: {
    airports: { PEK: 30, PKX: 50 },
    zones: {
      'peninsula': { dist: 3, zone: 'Wangfujing', airport: 'PEK' },
      'rosewood': { dist: 3, zone: 'Chaoyang', airport: 'PEK' },
      'waldorf astoria': { dist: 2, zone: 'Wangfujing', airport: 'PEK' },
      'park hyatt': { dist: 3, zone: 'CBD', airport: 'PEK' },
      'opposite house': { dist: 4, zone: 'Sanlitun', airport: 'PEK' },
      'aman': { dist: 15, zone: 'Summer Palace', airport: 'PEK' },
      'four seasons': { dist: 3, zone: 'Chaoyang', airport: 'PEK' },
      'st regis': { dist: 3, zone: 'CBD', airport: 'PEK' },
      'ritz carlton': { dist: 3, zone: 'CBD', airport: 'PEK' },
      'mandarin oriental': { dist: 3, zone: 'Wangfujing', airport: 'PEK' },
      'intercontinental': { dist: 3, zone: 'Sanlitun', airport: 'PEK' },
      'shangri-la': { dist: 4, zone: 'CBD', airport: 'PEK' },
      'grand hyatt': { dist: 3, zone: 'Dongcheng', airport: 'PEK' },
      'hilton': { dist: 4, zone: 'Chaoyang', airport: 'PEK' },
      'marriott': { dist: 4, zone: 'Chaoyang', airport: 'PEK' },
      'sheraton': { dist: 5, zone: 'Chaoyang', airport: 'PEK' },
      'westin': { dist: 3, zone: 'Financial Street', airport: 'PEK' },
      'conrad': { dist: 4, zone: 'Chaoyang', airport: 'PEK' },
      'w hotel': { dist: 4, zone: 'Chaoyang', airport: 'PEK' },
      'edition': { dist: 4, zone: 'Sanlitun', airport: 'PEK' },
      'andaz': { dist: 4, zone: 'Sanlitun', airport: 'PEK' },
      'banyan tree': { dist: 15, zone: 'Summer Palace', airport: 'PEK' },
      'guangdong hotel': { dist: 2, zone: 'Wangfujing', airport: 'PEK' },
      'cbd': { dist: 15, zone: 'CBD', airport: 'PEK' },
      'wangfujing': { dist: 3, zone: 'Wangfujing', airport: 'PEK' },
      'sanlitun': { dist: 6, zone: 'Sanlitun', airport: 'PEK' },
      'forbidden city': { dist: 3, zone: 'Forbidden City', airport: 'PEK' },
      'tiananmen': { dist: 3, zone: 'Tiananmen', airport: 'PEK' },
      'chaoyang': { dist: 10, zone: 'Chaoyang', airport: 'PEK' },
      'haidian': { dist: 15, zone: 'Haidian', airport: 'PEK' },
      'dongcheng': { dist: 5, zone: 'Dongcheng', airport: 'PEK' },
      'xicheng': { dist: 5, zone: 'Xicheng', airport: 'PEK' },
      'fengtai': { dist: 12, zone: 'Fengtai', airport: 'PEK' },
      'shijingshan': { dist: 25, zone: 'Shijingshan', airport: 'PEK' },
      'tongzhou': { dist: 20, zone: 'Tongzhou', airport: 'PEK' },
      'shunyi': { dist: 15, zone: 'Shunyi', airport: 'PEK' },
      'daxing': { dist: 20, zone: 'Daxing', airport: 'PEK' },
      'changping': { dist: 25, zone: 'Changping', airport: 'PEK' },
      'yanqing': { dist: 50, zone: 'Yanqing', airport: 'PEK' },
      'huairou': { dist: 40, zone: 'Huairou', airport: 'PEK' },
      'mentougou': { dist: 30, zone: 'Mentougou', airport: 'PEK' },
      'pinggu': { dist: 45, zone: 'Pinggu', airport: 'PEK' },
      'miyun': { dist: 50, zone: 'Miyun', airport: 'PEK' },
      'fangshan': { dist: 25, zone: 'Fangshan', airport: 'PEK' },
      'default': { dist: 25, zone: 'City Center', airport: 'PEK' }
    }
  }
};
```

---

## 匹配算法

```javascript
function smartDistanceEstimate(address, city, airport) {
  if (!address || !city) return null;

  const cityData = cityZones[city];
  if (!cityData) return null;

  const lowerAddr = address.toLowerCase().trim();
  const zones = cityData.zones;

  // 1. 精确匹配（酒店名）
  for (const [keyword, data] of Object.entries(zones)) {
    if (keyword === 'default') continue;
    if (lowerAddr.includes(keyword.toLowerCase())) {
      return data;
    }
  }

  // 2. 回退默认
  return zones['default'] || { dist: 25, zone: 'City Center', airport: Object.keys(cityData.airports)[0] };
}

function getDistanceRange(dist) {
  if (dist <= 30) return '0-30';
  if (dist <= 50) return '30-50';
  if (dist <= 80) return '50-80';
  return '80+';
}
```

---

## 用户交互流程

```
用户选择城市 → 自动更新机场列表
       ↓
用户选择机场 → 显示"到市中心约 X km"提示
       ↓
用户输入酒店地址 → 实时关键词匹配
       ↓
   [匹配成功] → 自动填充距离范围 + 显示区域名
   [匹配失败] → 保持默认距离 + 提示"请手动调整"
       ↓
用户可手动调整距离范围（下拉菜单）
       ↓
系统自动计算价格 = 基础价 × 城市系数 × 距离系数
```

---

## 示例交互

**场景 1：上海浦东机场到外滩酒店**
```
城市：Shanghai
机场：Shanghai Pudong (PVG) ~45 km
地址：The Peninsula Shanghai, The Bund
→ 匹配关键词 "peninsula" 和 "bund"
→ 自动距离 = 2 km + 机场到市中心 45 km
→ 距离范围 = 30-50 km
→ 价格 = $51 × 1.0 × 1.3 = $66.3 → 四舍五入 $65
```

**场景 2：北京首都机场到国贸酒店**
```
城市：Beijing
机场：Beijing Capital (PEK) ~30 km
地址：Park Hyatt Beijing, CBD
→ 匹配关键词 "park hyatt" 和 "cbd"
→ 自动距离 = 3 km + 机场到市中心 30 km
→ 距离范围 = 30-50 km
→ 价格 = $51 × 1.0 × 1.3 = $66.3 → 四舍五入 $65
```

**场景 3：输入不认识的地址**
```
城市：Shanghai
机场：PVG
地址：某个不知名的小区
→ 没有匹配到任何关键词
→ 回退默认距离 = 25 km + 机场 45 km = 70 km
→ 距离范围 = 50-80 km
→ 提示："地址未识别，已使用默认距离。请手动调整范围"
```

---

## 覆盖范围估算

| 城市 | 酒店数量 | 区域数量 | 覆盖率估算 |
|------|----------|----------|------------|
| 上海 | 25+ | 20+ | 80-90% |
| 北京 | 25+ | 18+ | 80-90% |
| 广州 | 15+ | 15+ | 70-80% |
| 深圳 | 15+ | 12+ | 70-80% |
| 成都 | 12+ | 10+ | 65-75% |
| 其他城市 | 8+ | 8+ | 50-60% |

> 未覆盖的地址自动回退到默认距离，用户可手动调整。后续可根据实际预订数据持续补充关键词。

---

## 实现方式

1. 创建一个 `js/distance.js` 文件，包含 `cityZones` 数据库
2. 在 `booking.html` 中引入 `distance.js`
3. 在地址输入框添加 `oninput` 事件，实时触发 `smartDistanceEstimate`
4. 匹配结果自动更新距离下拉菜单和 `distanceInfo` 提示文本

---

## 优点总结

| 特性 | 说明 |
|------|------|
| **零外部依赖** | 纯 JavaScript，不需要 Google Maps、高德、百度等任何 API |
| **全球可用** | 不受 GFW 影响，海外客户直接使用 |
| **无需备案** | 不需要国内 ICP 或企业资质 |
| **实时响应** | 输入即计算，无需等待 API 返回 |
| **离线可用** | 所有数据在本地，网络不稳定也能工作 |
| **可扩展** | 根据实际预订数据持续添加新关键词，越用越准 |
| **透明** | 距离逻辑完全在客户端，客户可看到计算过程 |

---

## 实现计划

**Phase 1**（今天）：上海、北京、广州、深圳（Tier 1）
**Phase 2**（本周）：成都、杭州、武汉、重庆、南京（Tier 2）
**Phase 3**（后续）：根据客户反馈持续补充
