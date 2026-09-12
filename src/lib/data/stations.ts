export interface StationOption {
	id: string;
	name: string;
	lat: number | null;
	lng: number | null;
}

export const stationOptions: StationOption[] = [
	{ id: '', name: '駅を選択してください', lat: null, lng: null },
	{ id: 'minami-nagareyama', name: '南流山', lat: 35.8381, lng: 139.9035 },
	{ id: 'nagareyama-central-park', name: '流山セントラルパーク', lat: 35.8546, lng: 139.9152 },
	{ id: 'nagareyama-otakanomori', name: '流山おおたかの森', lat: 35.8719, lng: 139.9254 },
	{ id: 'kashiwanoha-campus', name: '柏の葉キャンパス', lat: 35.8933, lng: 139.9525 },
	{ id: 'kashiwa-tanaka', name: '柏たなか', lat: 35.9109, lng: 139.9575 },
	{ id: 'moriya', name: '守谷', lat: 35.9504, lng: 139.9921 },
	{ id: 'mirai-daira', name: 'みらい平', lat: 35.9944, lng: 140.0383 },
	{ id: 'midorino', name: 'みどりの', lat: 36.0299, lng: 140.0562 },
	{ id: 'kenkyugakuen', name: '研究学園', lat: 36.0822, lng: 140.0823 },
	{ id: 'banpaku-kinen-koen', name: '万博記念公園', lat: 36.0584, lng: 140.0594 },
	{ id: 'tsukuba', name: 'つくば', lat: 36.0824, lng: 140.1105 },
	{ id: 'matsudo', name: '松戸', lat: 35.7846, lng: 139.9008 },
	{ id: 'kashiwa', name: '柏', lat: 35.8621, lng: 139.9708 },
	{ id: 'shin-matsudo', name: '新松戸', lat: 35.8254, lng: 139.9212 },
	{ id: 'minami-kashiwa', name: '南柏', lat: 35.8446, lng: 139.9542 },
	{ id: 'abiko', name: '我孫子', lat: 35.8728, lng: 140.0105 },
	{ id: 'toride', name: '取手', lat: 35.8963, lng: 140.0632 },
	{ id: 'edogawadai', name: '江戸川台', lat: 35.8972, lng: 139.9105 },
	{ id: 'hatsuishi', name: '初石', lat: 35.8838, lng: 139.9179 },
	{ id: 'unga', name: '運河', lat: 35.9144, lng: 139.906 },
	{ id: 'shimizu-koen', name: '清水公園', lat: 35.9588, lng: 139.8603 },
	{ id: 'nagareyama', name: '流山', lat: 35.8558, lng: 139.9018 },
	{ id: 'toyoshiki', name: '豊四季', lat: 35.8665, lng: 139.9393 },
	{ id: 'sakasai', name: '逆井', lat: 35.8233, lng: 139.9837 },
	{ id: 'shin-yahashira', name: '新八柱', lat: 35.7913, lng: 139.9386 }
];
