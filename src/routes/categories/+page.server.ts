import { categoryOptions } from '$lib/data/categories';
import { filterPOIsByCategory, loadPOIData } from '$lib/server/poi';
import type { PageServerLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

export const load: PageServerLoad = async () => {
	const pois = await loadPOIData();

	return {
		categories: categoryOptions.map((category) => ({
			...category,
			count: filterPOIsByCategory(pois, category.keywords).length
		}))
	};
};
