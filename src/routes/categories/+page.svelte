<script lang="ts">
	import { base } from '$app/paths';
	import type { PageData } from './$types';

	export let data: PageData;
</script>

<svelte:head>
	<title>東葛・TX沿線のカテゴリ別まとめ | ちーぶろマップ</title>
	<meta
		name="description"
		content="東葛地域とつくばエクスプレス沿線のカフェ、ラーメン、寿司、洋食、居酒屋、公園をカテゴリ別に探せます。"
	/>
</svelte:head>

<main class="h-screen overflow-y-auto bg-gradient-to-br from-slate-50 to-slate-100 p-4 md:p-8">
	<div class="mx-auto max-w-4xl rounded-2xl bg-white p-6 shadow-lg md:p-10">
		<nav aria-label="パンくず" class="mb-6 text-sm text-slate-500">
			<!-- eslint-disable svelte/no-navigation-without-resolve -->
			<a href={`${base}/`} class="text-sky-600 hover:underline">地図トップ</a>
			<!-- eslint-enable svelte/no-navigation-without-resolve -->
			<span class="mx-2" aria-hidden="true">›</span>
			<span aria-current="page">カテゴリ別まとめ</span>
		</nav>

		<header class="mb-8 border-b border-slate-200 pb-6">
			<h1 class="text-2xl font-bold text-slate-800 md:text-3xl">東葛・TX沿線のカテゴリ別まとめ</h1>
			<p class="mt-3 text-slate-600">
				地域ブログで紹介されたスポットを、目的に合わせてカテゴリから探せます。
			</p>
		</header>

		<ul class="grid gap-4 sm:grid-cols-2">
			{#each data.categories as category (category.id)}
				<li>
					<!-- eslint-disable svelte/no-navigation-without-resolve -->
					<a
						href={`${base}/categories/${category.id}`}
						class="group flex h-full flex-col rounded-xl border border-slate-200 p-5 transition hover:border-sky-300 hover:bg-sky-50 hover:shadow-md"
					>
						<!-- eslint-enable svelte/no-navigation-without-resolve -->
						<div class="flex items-center justify-between gap-4">
							<h2 class="text-xl font-semibold text-slate-800 group-hover:text-sky-700">
								{category.label}
							</h2>
							<span class="rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-700">
								{category.count}件
							</span>
						</div>
						<p class="mt-3 flex-1 text-sm leading-6 text-slate-600">{category.description}</p>
						<span class="mt-4 text-sm font-medium text-sky-600">記事を見る →</span>
					</a>
				</li>
			{/each}
		</ul>
	</div>
</main>
