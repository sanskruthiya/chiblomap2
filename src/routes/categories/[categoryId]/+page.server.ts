import { error } from '@sveltejs/kit';
import { categoryOptions } from '$lib/data/categories';
import { stationOptions } from '$lib/data/stations';
import { loadPOIData, filterPOIsByCategory } from '$lib/server/poi';
import type { PageServerLoad } from './$types';

export const entries = () => {
	return categoryOptions.map((category) => ({ categoryId: category.id }));
};

export const prerender = true;

const EARTH_RADIUS_M = 6_371_000;

function toRad(deg: number): number {
	return (deg * Math.PI) / 180;
}

function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
	const dLat = toRad(lat2 - lat1);
	const dLon = toRad(lon2 - lon1);
	const a =
		Math.sin(dLat / 2) * Math.sin(dLat / 2) +
		Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
	const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
	return EARTH_RADIUS_M * c;
}

export const load: PageServerLoad = async ({ params }) => {
	const category = categoryOptions.find((c) => c.id === params.categoryId);

	if (!category) {
		error(404, 'カテゴリが見つかりません');
	}

	const allPOIs = await loadPOIData();
	const matchedPOIs = filterPOIsByCategory(allPOIs, category.keywords).sort(
		(a, b) => (b.properties.date_stamp ?? 0) - (a.properties.date_stamp ?? 0)
	);

	const stations = stationOptions.filter((s) => s.lat != null && s.lng != null);

	const pois = matchedPOIs.slice(0, 100).map((poi) => {
		const [lng, lat] = poi.geometry.coordinates;
		const distances: Record<string, number> = {};
		for (const station of stations) {
			distances[station.id] = haversineMeters(
				lat,
				lng,
				station.lat as number,
				station.lng as number
			);
		}
		return { ...poi, distances };
	});

	return {
		category,
		pois,
		totalCount: matchedPOIs.length
	};
};
