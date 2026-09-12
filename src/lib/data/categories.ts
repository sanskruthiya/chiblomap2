export interface CategoryOption {
	id: string;
	label: string;
	keywords: string[];
}

export const categoryOptions: CategoryOption[] = [
	{ id: 'cafe', label: 'カフェ', keywords: ['カフェ', 'cafe', '喫茶店', 'コーヒー', 'coffee'] },
	{ id: 'ramen', label: 'ラーメン', keywords: ['ラーメン', 'ramen', 'らーめん', '麺屋'] },
	{ id: 'sushi', label: '寿司', keywords: ['寿司', '鮨'] },
	{ id: 'westernfood', label: '洋食', keywords: ['レストラン', 'イタリアン', 'フレンチ'] },
	{ id: 'izakaya', label: '居酒屋', keywords: ['居酒屋', '呑み'] },
	{ id: 'park', label: '公園', keywords: ['公園'] }
];
