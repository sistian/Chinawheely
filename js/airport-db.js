// Chinawheely 机场库 v1.0
// 覆盖全部 53 个有报价城市（与 pricing/pricing.json 的城市集合一致）。
// dist = 机场到市中心车程公里数（用于自动预填距离区间 + 接送机参考时长）。
// 与 js/distance-db.js 的 cityZones（19 城酒店关键词库）配合使用：
//   getAirportsForCity() 先查 cityZones，缺失时回落到本表。

const AIRPORT_DB = {
  // ---- 华北 ----
  beijing: [{ code: 'PEK', name: 'Beijing Capital (PEK)', dist: 30 },
            { code: 'PKX', name: 'Beijing Daxing (PKX)', dist: 50 }],
  tianjin: [{ code: 'TSN', name: 'Tianjin Binhai (TSN)', dist: 25 }],
  shijiazhuang: [{ code: 'SJW', name: 'Shijiazhuang Zhengding (SJW)', dist: 30 }],
  taiyuan: [{ code: 'TYN', name: 'Taiyuan Wusu (TYN)', dist: 15 }],
  hohhot: [{ code: 'HET', name: 'Hohhot Baita (HET)', dist: 25 }],
  xianyang: [{ code: 'XIY', name: "Xianyang Xianyang (XIY)", dist: 32 }],

  // ---- 华东 ----
  shanghai: [{ code: 'PVG', name: 'Shanghai Pudong (PVG)', dist: 45 },
             { code: 'SHA', name: 'Shanghai Hongqiao (SHA)', dist: 15 }],
  hangzhou: [{ code: 'HGH', name: 'Hangzhou Xiaoshan (HGH)', dist: 30 }],
  nanjing: [{ code: 'NKG', name: 'Nanjing Lukou (NKG)', dist: 35 }],
  suzhou: [{ code: 'SHA', name: 'Shanghai Hongqiao (SHA)', dist: 80 },
           { code: 'WUX', name: 'Wuxi Sunan Shuofang (WUX)', dist: 60 }],
  wuxi: [{ code: 'WUX', name: 'Wuxi Sunan Shuofang (WUX)', dist: 20 }],
  changzhou: [{ code: 'WUX', name: 'Wuxi Sunan Shuofang (WUX)', dist: 55 },
              { code: 'NKG', name: 'Nanjing Lukou (NKG)', dist: 95 }],
  yangzhou: [{ code: 'NKG', name: 'Nanjing Lukou (NKG)', dist: 60 }],
  ningbo: [{ code: 'NGB', name: 'Ningbo Lishe (NGB)', dist: 22 }],
  wenzhou: [{ code: 'WNZ', name: 'Wenzhou Longwan (WNZ)', dist: 25 }],
  jiaxing: [{ code: 'SHA', name: 'Shanghai Hongqiao (SHA)', dist: 85 },
            { code: 'HGH', name: 'Hangzhou Xiaoshan (HGH)', dist: 90 }],
  shaoxing: [{ code: 'HGH', name: 'Hangzhou Xiaoshan (HGH)', dist: 60 },
             { code: 'SHA', name: 'Shanghai Hongqiao (SHA)', dist: 95 }],
  taizhou: [{ code: 'HGH', name: 'Hangzhou Xiaoshan (HGH)', dist: 130 },
            { code: 'WNZ', name: 'Wenzhou Longwan (WNZ)', dist: 150 }],
  jinhua: [{ code: 'YIW', name: 'Yiwu Yiwu (YIW)', dist: 30 },
            { code: 'HGH', name: 'Hangzhou Xiaoshan (HGH)', dist: 90 }],
  jinan: [{ code: 'TNA', name: 'Jinan Yaoqiang (TNA)', dist: 28 }],
  qingdao: [{ code: 'TAO', name: 'Qingdao Liuting (TAO)', dist: 32 }],
  yantai: [{ code: 'YNT', name: 'Yantai Penglai (YNT)', dist: 40 }],
  weihai: [{ code: 'WEH', name: 'Weihai Daxue (WEH)', dist: 45 }],
  fuzhou: [{ code: 'FOC', name: 'Fuzhou Changle (FOC)', dist: 50 }],
  xiamen: [{ code: 'XMN', name: 'Xiamen Gaoqi (XMN)', dist: 12 }],
  quanzhou: [{ code: 'JJN', name: 'Quanzhou Jinjiang (JJN)', dist: 15 }],
  nanchang: [{ code: 'KHN', name: 'Nanchang Changbei (KHN)', dist: 30 }],
  hefei: [{ code: 'HFE', name: 'Hefei Xinqiao (HFE)', dist: 32 }],

  // ---- 华南 ----
  guangzhou: [{ code: 'CAN', name: 'Guangzhou Baiyun (CAN)', dist: 30 }],
  shenzhen: [{ code: 'SZX', name: 'Shenzhen Baoan (SZX)', dist: 32 }],
  dongguan: [{ code: 'SZX', name: 'Shenzhen Baoan (SZX)', dist: 45 }],
  huizhou: [{ code: 'SZX', name: 'Shenzhen Baoan (SZX)', dist: 55 }],
  foshan: [{ code: 'CAN', name: 'Guangzhou Baiyun (CAN)', dist: 40 }],
  zhongshan: [{ code: 'CAN', name: 'Guangzhou Baiyun (CAN)', dist: 45 }],
  zhuhai: [{ code: 'ZUH', name: 'Zhuhai Jinwan (ZUH)', dist: 35 }],
  sanya: [{ code: 'SYX', name: 'Sanya Phoenix (SYX)', dist: 14 }],
  haikou: [{ code: 'HAK', name: 'Haikou Meilan (HAK)', dist: 15 }],

  // ---- 西南 ----
  chengdu: [{ code: 'CTU', name: 'Chengdu Shuangliu (CTU)', dist: 16 },
            { code: 'TFU', name: 'Chengdu Tianfu (TFU)', dist: 50 }],
  chongqing: [{ code: 'CKG', name: 'Chongqing Jiangbei (CKG)', dist: 30 }],
  kunming: [{ code: 'KMG', name: 'Kunming Changshui (KMG)', dist: 32 }],
  guiyang: [{ code: 'KWE', name: 'Guiyang Longdongbao (KWE)', dist: 30 }],

  // ---- 华中 ----
  wuhan: [{ code: 'WUH', name: 'Wuhan Tianhe (WUH)', dist: 24 }],
  changsha: [{ code: 'CSX', name: 'Changsha Huanghua (CSX)', dist: 30 }],
  zhengzhou: [{ code: 'CGO', name: 'Zhengzhou Xinzheng (CGO)', dist: 32 }],
  luoyang: [{ code: 'LLY', name: 'Luoyang Beijiao (LLY)', dist: 25 }],

  // ---- 东北 ----
  shenyang: [{ code: 'SHE', name: 'Shenyang Taoxian (SHE)', dist: 22 }],
  dalian: [{ code: 'DLC', name: 'Dalian Zhoushuizi (DLC)', dist: 13 }],
  changchun: [{ code: 'CGQ', name: 'Changchun Longjia (CGQ)', dist: 32 }],
  harbin: [{ code: 'HRB', name: 'Harbin Taiping (HRB)', dist: 32 }],

  // ---- 西北 ----
  xian: [{ code: 'XIY', name: "Xi'an Xianyang (XIY)", dist: 32 }],
  yinchuan: [{ code: 'INC', name: 'Yinchuan Hedong (INC)', dist: 20 }],
  urumqi: [{ code: 'URC', name: 'Urumqi Diwopu (URC)', dist: 20 }],

  // ---- 西南其他 ----
  nanning: [{ code: 'NNG', name: 'Nanning Wuxu (NNG)', dist: 32 }],
};

// 清理占位（空数组的城市不应存在）
Object.keys(AIRPORT_DB).forEach(function (k) {
  if (!AIRPORT_DB[k] || !AIRPORT_DB[k].length) delete AIRPORT_DB[k];
});

if (typeof window !== 'undefined') {
  window.AIRPORT_DB = AIRPORT_DB;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AIRPORT_DB: AIRPORT_DB };
}
