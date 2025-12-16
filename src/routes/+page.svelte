<script lang="ts">
	import { onMount } from 'svelte';
	import Map from '$lib/components/Map.svelte';
	import LoadingScreen from '$lib/components/LoadingScreen.svelte';

	let isLoading = true;
	let loadedCount = 0;
	let totalCount = 0;
	let mapComponent: Map;

	// ローディング完了時の処理
	function handleLoadingReady() {
		isLoading = false;
	}

	// POI読み込み進捗の更新
	function handleLoadingProgress(event: CustomEvent) {
		loadedCount = event.detail.loadedCount;
		totalCount = event.detail.totalCount;
	}
</script>

<svelte:head>
	<title>ちーぶろマップ</title>
	<meta name="description" content="千葉県のおすすめスポットを探せるマップ" />
</svelte:head>

<main class="h-screen w-full relative">
	{#if isLoading}
		<LoadingScreen 
			{loadedCount} 
			{totalCount} 
			{isLoading}
			on:ready={handleLoadingReady}
		/>
	{/if}
	
	<Map 
		bind:this={mapComponent}
		on:loadingProgress={handleLoadingProgress}
		showInitially={!isLoading}
	/>
</main>
