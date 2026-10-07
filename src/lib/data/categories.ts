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
		id: 'westernfood',
		label: '洋食',
		description: 'レストランやイタリアン、フレンチの記事を集めました。',
		keywords: ['レストラン', 'イタリアン', 'フレンチ']
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
