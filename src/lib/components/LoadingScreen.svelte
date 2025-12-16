<script lang="ts">
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let loadedCount = 0;
	export let totalCount = 0;
	export let isLoading = true;

	let siteInfo: any = null;
	let progress = 0;

	$: progress = totalCount > 0 ? Math.round((loadedCount / totalCount) * 100) : 0;

	onMount(async () => {
		try {
			const response = await fetch('/data/site-info.json');
			siteInfo = await response.json();
		} catch (error) {
			console.error('サイト情報の読み込みに失敗しました:', error);
		}
	});

	// 一定の進捗でマップを表示
	$: if (progress >= 30 && isLoading) {
		setTimeout(() => {
			dispatch('ready');
		}, 1000);
	}
</script>

<div class="loading-screen">
	<div class="loading-content">
		<!-- 猫のロゴ -->
		<div class="logo-container">
			<img src="/chiblogo.webp" alt="Chiblo Map" class="logo" />
		</div>

		<!-- タイトル -->
		<h1 class="title">ちーぶろマップ</h1>
		<p class="subtitle">東葛・TX沿線エリアのブログ記事まとめサイト</p>

		<!-- 進捗バー -->
		<div class="progress-container">
			<div class="progress-bar">
				<div class="progress-fill" style="width: {progress}%"></div>
			</div>
			<div class="progress-text">
				{#if totalCount > 0}
					{loadedCount} / {totalCount} 件読み込み中... ({progress}%)
				{:else}
					データを読み込み中...
				{/if}
			</div>
		</div>

		<!-- サイト情報 -->
		{#if siteInfo}
			<div class="site-info">
				<p class="update-info">
					最終更新: {siteInfo.lastDataUpdate}
				</p>
				<p class="data-count">
					総データ数: {siteInfo.dataCount.toLocaleString()} 件
				</p>
			</div>
		{/if}

		<!-- ローディングアニメーション -->
		<div class="loading-animation">
			<div class="spinner"></div>
		</div>
	</div>
</div>

<style>
	.loading-screen {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9999;
	}

	.loading-content {
		text-align: center;
		color: #333;
		max-width: 400px;
		padding: 2rem;
	}

	.logo-container {
		margin-bottom: 1.5rem;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.logo {
		width: 120px;
		height: 120px;
		border-radius: 16px;
		box-shadow: 0 8px 32px rgba(82, 194, 208, 0.3);
		animation: float 3s ease-in-out infinite;
		display: block;
	}

	@keyframes float {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-10px); }
	}

	.title {
		font-size: 2rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
		color: #52c2d0;
		text-shadow: none;
	}

	.subtitle {
		font-size: 0.8rem;
		margin-bottom: 2rem;
		color: #6c757d;
	}

	.progress-container {
		margin-bottom: 2rem;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: rgba(108, 117, 125, 0.2);
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #52c2d0 0%, #45a8b5 100%);
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.9rem;
		color: #6c757d;
	}

	.site-info {
		margin-bottom: 2rem;
		padding: 1rem;
		background: rgba(255, 255, 255, 0.8);
		border: 1px solid rgba(82, 194, 208, 0.2);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.update-info, .data-count {
		margin: 0.25rem 0;
		font-size: 0.9rem;
	}

	.loading-animation {
		display: flex;
		justify-content: center;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid rgba(82, 194, 208, 0.3);
		border-top: 3px solid #52c2d0;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
</style>
