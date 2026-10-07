import { error } from '@sveltejs/kit';
import { categoryOptions } from '$lib/data/categories';
import { loadPOIData, filterPOIsByCategory } from '$lib/server/poi';
import type { PageServerLoad } from './$types';

export const entries = () => {
	return categoryOptions.map((category) => ({ categoryId: category.id }));
};

export const prerender = true;

export const load: PageServerLoad = async ({ params }) => {
	const category = categoryOptions.find((c) => c.id === params.categoryId);

	if (!category) {
		error(404, 'カテゴリが見つかりません');
	}

	const allPOIs = await loadPOIData();
	const matchedPOIs = filterPOIsByCategory(allPOIs, category.keywords).sort(
		(a, b) => (b.properties.date_stamp ?? 0) - (a.properties.date_stamp ?? 0)
	);

	return {
		category,
		pois: matchedPOIs.slice(0, 100),
		totalCount: matchedPOIs.length
	};
};
