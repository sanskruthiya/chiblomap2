import fs from 'node:fs';
import path from 'node:path';
import { Readable } from 'node:stream';
import { deserialize } from 'flatgeobuf/lib/mjs/geojson.js';
import type { POIFeature } from '$lib/types/poi';

let cachedPOIs: POIFeature[] | null = null;

export async function loadPOIData(): Promise<POIFeature[]> {
	if (cachedPOIs) return cachedPOIs;

	// adapter-static プリレンダリング時に static/data/poi.fgb を読み込む
	// vite build はプロジェクトルートで実行される前提
	const filePath = path.join(process.cwd(), 'static/data/poi.fgb');
	const fileStream = fs.createReadStream(filePath);
	const webStream = Readable.toWeb(fileStream) as unknown as ReadableStream<Uint8Array>;

	const features: POIFeature[] = [];
	const iter = deserialize(webStream);

	for await (const feature of iter) {
		features.push(feature as unknown as POIFeature);
	}

	cachedPOIs = features;
	return features;
}

export function filterPOIsByCategory(pois: POIFeature[], keywords: string[]): POIFeature[] {
	if (keywords.length === 0) return pois;

	const lowerKeywords = keywords.map((k) => k.toLowerCase());

	return pois.filter((poi) => {
		const props = poi.properties;
		if (!props) return false;
		const targets = [props.name_poi || '', props.title_source || ''];
		return lowerKeywords.some((keyword) =>
			targets.some((target) => target.toLowerCase().includes(keyword))
		);
	});
}

export function filterPOIsByKeywords(
	pois: POIFeature[],
	searchTargets: (keyof POIFeature['properties'])[] = ['name_poi', 'title_source'],
	keywords: string[]
): POIFeature[] {
	if (keywords.length === 0) return pois;
	const lowerKeywords = keywords.map((k) => k.toLowerCase());

	return pois.filter((poi) => {
		const props = poi.properties;
		if (!props) return false;
		const targets = searchTargets.map((key) => String(props[key] || ''));
		return lowerKeywords.some((keyword) =>
			targets.some((target) => target.toLowerCase().includes(keyword))
		);
	});
}
