export interface CategoryOption {
	id: string;
	label: string;
	description: string;
	keywords: string[];
}

export const categoryOptions: CategoryOption[] = [
	{
		id: 'cafe',
		label: 'カフェ',
		description: 'コーヒーやスイーツ、ランチを楽しめるカフェを探せます。',
		keywords: ['カフェ', 'cafe', '喫茶店', 'コーヒー', 'coffee']
	},
	{
		id: 'ramen',
		label: 'ラーメン',
		description: '地域ブログで紹介されたラーメン店をまとめています。',
		keywords: ['ラーメン', 'ramen', 'らーめん', '麺屋']
	},
	{
		id: 'sushi',
		label: '寿司',
		description: '東葛・TX沿線で楽しめる寿司店を紹介します。',
		keywords: ['寿司', '鮨']
	},
	{
		id: 'sweets',
		label: 'スイーツ・デザート',
		description: 'ケーキ、和菓子、かき氷、パンケーキなどのスイーツ店を紹介します。',
		keywords: [
			'スイーツ',
			'デザート',
			'ケーキ',
			'タルト',
			'プリン',
			'パンケーキ',
			'かき氷',
			'ワッフル',
			'クレープ',
			'ドーナツ',
			'和菓子',
			'大福',
			'パティスリー',
			'patisserie'
		]
	},
	{
		id: 'bakery',
		label: 'パン・ベーカリー',
		description: 'こだわりのパン屋・ベーカリーをまとめています。',
		keywords: [
			'パン屋',
			'ブランジェリー',
			'ブーランジェリー',
			'boulangerie',
			'boulanger',
			'惣菜パン',
			'製パン',
			'パン工房',
			'ベーカリー',
			'bakery',
			'サンドイッチ',
			'クロワッサン',
			'バゲット'
		]
	},
	{
		id: 'afternoontea',
		label: 'アフタヌーンティー',
		description: 'ホテルやカフェで楽しめるアフタヌーンティーを紹介します。',
		keywords: ['アフタヌーンティ', 'アフタヌーン・ティ']
	},
	{
		id: 'chinese',
		label: '中華',
		description: '東葛・TX沿線の中華料理店をまとめています。',
		keywords: ['中華', 'チャイニーズ', '中国料理', '餃子', '小籠包', '担々麺', '麻婆豆腐', '四川']
	},
	{
		id: 'curry',
		label: 'カレー',
		description: 'スパイスカレーからインドカレーまで、カレー専門店をまとめています。',
		keywords: ['カレー', 'curry']
	},
	{
		id: 'westernfood',
		label: '洋食',
		description: '洋食、イタリアン、フレンチ、ビストロなどの記事を集めました。',
		keywords: ['洋食', 'イタリアン', 'フレンチ', 'ビストロ', 'ステーキ', 'ハンバーグ']
	},
	{
		id: 'izakaya',
		label: '居酒屋',
		description: '地元で立ち寄りたい居酒屋の記事を探せます。',
		keywords: ['居酒屋', '呑み']
	},
	{
		id: 'park',
		label: '公園',
		description: '家族のお出かけや散歩に使える公園をまとめています。',
		keywords: ['公園']
	}
];
