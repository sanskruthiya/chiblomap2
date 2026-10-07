<script lang="ts">
	import { base } from '$app/paths';
	import { categoryOptions } from '$lib/data/categories';
	import { stationOptions } from '$lib/data/stations';
	import type { PageData } from './$types';

	export let data: PageData;

	const STATION_RADIUS_M = 2000;

	$: category = data.category;
	$: pois = data.pois.slice(0, 100);
	$: totalCount = data.totalCount;

	let selectedStationId = '';

	const stations = stationOptions.filter((s) => s.lat != null && s.lng != null);

	$: filteredPOIs = selectedStationId
		? pois
				.filter((poi) => (poi.distances[selectedStationId] ?? Infinity) <= STATION_RADIUS_M)
				.sort((a, b) => a.distances[selectedStationId] - b.distances[selectedStationId])
		: pois;

	$: displayCount = selectedStationId ? filteredPOIs.length : totalCount;

	function officialLinkLabel(flag: string) {
		const labels: Record<string, string> = {
			'1': '公式サイト',
			'2': 'Instagram',
			'3': 'Twitter'
		};
		return labels[flag] ?? 'リンク';
	}
</script>

<svelte:head>
	<title>東葛・TX沿線の{category.label}まとめ | ちーぶろマップ</title>
	<meta
		name="description"
		content="東葛地域とつくばエクスプレス沿線の{category.label}を紹介する地域ブログ記事をまとめました。{totalCount}件のスポットを地図から探せます。"
	/>
</svelte:head>

<main class="h-screen overflow-y-auto bg-gradient-to-br from-slate-50 to-slate-100 p-4 md:p-8">
	<div class="mx-auto max-w-4xl rounded-2xl bg-white p-6 shadow-lg md:p-10">
		<nav aria-label="パンくず" class="mb-6 text-sm text-slate-500">
			<!-- eslint-disable svelte/no-navigation-without-resolve -->
			<a href={`${base}/`} class="text-sky-600 hover:underline">地図トップ</a>
			<span class="mx-2" aria-hidden="true">›</span>
			<a href={`${base}/categories/`} class="text-sky-600 hover:underline">カテゴリ別まとめ</a>
			<!-- eslint-enable svelte/no-navigation-without-resolve -->
			<span class="mx-2" aria-hidden="true">›</span>
			<span aria-current="page">{category.label}</span>
		</nav>

		<header class="mb-8 border-b border-slate-200 pb-6">
			<h1 class="text-2xl font-bold text-slate-800 md:text-3xl">
				東葛・TX沿線の{category.label}まとめ
			</h1>
			<p class="mt-2 text-slate-600">
				柏市・流山市・松戸市・野田市・我孫子市・守谷市などの{category.label}を紹介する地域ブログ記事を集めました。
			</p>
			<div class="mt-4 flex flex-wrap items-center gap-3">
				<span class="rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-700">
					該当スポット: {displayCount}件
				</span>
				<label class="flex items-center gap-2 text-sm text-slate-600">
					<span>駅から絞り込み（2km圏内）:</span>
					<select
						bind:value={selectedStationId}
						class="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
					>
						<option value="">すべての駅</option>
						{#each stations as station (station.id)}
							<option value={station.id}>{station.name}</option>
						{/each}
					</select>
				</label>
			</div>
			<p class="mt-2 text-xs text-slate-500">
				※駅からの距離は直線距離（概算）です。
			</p>
		</header>

		<nav aria-label="カテゴリを切り替える" class="mb-8">
			<h2 class="mb-3 text-sm font-semibold text-slate-600">カテゴリを切り替える</h2>
			<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-6">
				{#each categoryOptions as option (option.id)}
					{#if option.id === category.id}
						<span
							aria-current="page"
							class="rounded-lg bg-sky-500 px-3 py-2 text-center text-sm font-medium text-white"
						>
							{option.label}
						</span>
					{:else}
						<!-- eslint-disable svelte/no-navigation-without-resolve -->
						<a
							href={`${base}/categories/${option.id}`}
							class="rounded-lg bg-slate-100 px-3 py-2 text-center text-sm font-medium text-slate-700 transition hover:bg-sky-100 hover:text-sky-700"
						>
							<!-- eslint-enable svelte/no-navigation-without-resolve -->
							{option.label}
						</a>
					{/if}
				{/each}
			</div>
		</nav>

		{#if filteredPOIs.length > 0}
			<ul class="space-y-3">
				{#each filteredPOIs as poi (poi.properties.fid)}
					<li
						class="rounded-xl border border-slate-100 bg-white p-4 shadow-sm transition hover:shadow-md"
					>
						<!-- eslint-disable svelte/no-navigation-without-resolve -->
						<a
							href={poi.properties.link_source}
							target="_blank"
							rel="external noopener noreferrer"
							class="block"
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<h2 class="text-lg font-semibold text-slate-800 hover:text-sky-600">
										{poi.properties.name_poi}
										{#if selectedStationId && poi.distances[selectedStationId] != null}
											<span class="ml-2 text-xs font-normal text-slate-500">
												（{Math.round(poi.distances[selectedStationId])}m）
											</span>
										{/if}
									</h2>
									<p class="mt-1 text-sm text-slate-500">
										{poi.properties.blog_source}
										<span class="mx-1">·</span>
										{poi.properties.date_text}
									</p>
									<p class="mt-2 text-sm text-slate-700">
										{poi.properties.title_source}
									</p>
								</div>
								<svg
									class="mt-1 h-5 w-5 flex-shrink-0 text-slate-400"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
								>
									<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
									<path d="M15 3h6v6"></path>
									<path d="M10 14 21 3"></path>
								</svg>
							</div>
						</a>
						<div class="mt-3 flex flex-wrap items-center gap-3">
							<a
								href={`${base}/?lat=${poi.geometry.coordinates[1]}&lng=${poi.geometry.coordinates[0]}&zoom=16`}
								class="inline-flex items-center gap-1 rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-sm font-medium text-sky-700 transition hover:bg-sky-100"
							>
								<!-- eslint-enable svelte/no-navigation-without-resolve -->
								<svg
									class="h-4 w-4"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
								>
									<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
									<circle cx="12" cy="10" r="3"></circle>
								</svg>
								地図で見る
							</a>
							{#if poi.properties.url_flag !== '0' && poi.properties.url_link}
								<!-- eslint-disable svelte/no-navigation-without-resolve -->
								<a
									href={poi.properties.url_link}
									target="_blank"
									rel="external noopener noreferrer"
									class="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:border-sky-200 hover:text-sky-700"
								>
									<svg
										class="h-4 w-4"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
									>
										<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
										<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
									</svg>
									{officialLinkLabel(poi.properties.url_flag ?? '')}
								</a>
								<!-- eslint-enable svelte/no-navigation-without-resolve -->
							{/if}
						</div>
					</li>
				{/each}
			</ul>

			{#if selectedStationId && filteredPOIs.length === 0}
				<p class="mt-4 rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-600">
					選択した駅の2km圏内に該当するスポットは見つかりませんでした。
				</p>
			{:else if totalCount > 100}
				<p class="mt-6 text-center text-sm text-slate-500">
					表示は最新・代表100件です。残り{totalCount - 100}件は地図からご覧ください。
				</p>
			{/if}
		{:else}
			<p class="rounded-xl bg-slate-50 p-8 text-center text-slate-600">
				該当するスポットが見つかりませんでした。
			</p>
		{/if}
	</div>
</main>
