<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { POIFeature } from '$lib/types/poi';

	const dispatch = createEventDispatcher<{
		toggle: void;
		toggleSize: void;
		changeSort: string;
	}>();

	export let showPOIList = true;
	export let isListExpanded = false;
	export let totalPOICount = 0;
	export let centerPOIs: POIFeature[] = [];
	export let sortMode = 'name-asc';
</script>

{#if showPOIList}
	<div class="poi-list-overlay" class:large-screen={isListExpanded}>
		<div class="poi-list-header">
			<div class="poi-list-title-section">
				<h3 class="poi-list-title">マップ中央付近の記事一覧</h3>
				<span class="poi-count-badge">{totalPOICount > 99 ? '99+' : totalPOICount}</span>
			</div>

			<!-- ソートボタン -->
			<div class="sort-controls" style="display: none;">
				<button
					class="sort-button"
					class:active={sortMode === 'name-asc'}
					on:click={() => dispatch('changeSort', 'name-asc')}
					aria-label="場所名順"
					title="場所名順（あいうえお順）"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M3 6h18M7 12h10M11 18h6"></path>
						<path d="M7 8l3-3 3 3"></path>
					</svg>
				</button>
				<button
					class="sort-button"
					class:active={sortMode === 'date-desc'}
					on:click={() => dispatch('changeSort', 'date-desc')}
					aria-label="日付の新しい順"
					title="日付の新しい順"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
						<line x1="16" y1="2" x2="16" y2="6"></line>
						<line x1="8" y1="2" x2="8" y2="6"></line>
						<line x1="3" y1="10" x2="21" y2="10"></line>
						<path d="M12 14l-3 3 3 3"></path>
					</svg>
				</button>
			</div>

			<div class="poi-list-controls">
				<button
					class="expand-button"
					on:click={() => dispatch('toggleSize')}
					aria-label={isListExpanded ? 'リストを縮小' : 'リストを拡大'}
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						{#if isListExpanded}
							<!-- 縮小アイコン: 下矢印 -->
							<path d="M6 9l6 6 6-6"></path>
						{:else}
							<!-- 拡大アイコン: 四角が大きくなる -->
							<path d="M15 3h6v6M14 10l6.1-6.1M9 21H3v-6M10 14l-6.1 6.1"></path>
						{/if}
					</svg>
				</button>
				<button
					class="collapse-button"
					on:click={() => dispatch('toggle')}
					aria-label="記事一覧を非表示"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>
		</div>

		<div class="poi-list-content">
			{#if centerPOIs.length > 0}
				{#each centerPOIs as poi (poi.properties.fid)}
					<!-- eslint-disable svelte/no-navigation-without-resolve -->
					<a
						href={poi.properties.link_source}
						target="_blank"
						rel="external noopener noreferrer"
						class="poi-item"
					>
						<strong>{poi.properties.name_poi}</strong>
						({poi.properties.blog_source}
						{poi.properties.date_text})
						{poi.properties.title_source}
					</a>
					<!-- eslint-enable svelte/no-navigation-without-resolve -->
					<hr class="poi-divider" />
				{/each}
			{:else}
				<p class="poi-count">マップ中央付近に記事がありません。</p>
			{/if}
		</div>
	</div>
{:else}
	<!-- POIリストが非表示の時の再表示ボタン -->
	<button class="show-list-button" on:click={() => dispatch('toggle')} aria-label="記事一覧を表示">
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
			<line x1="16" y1="2" x2="16" y2="6"></line>
			<line x1="8" y1="2" x2="8" y2="6"></line>
			<line x1="3" y1="10" x2="21" y2="10"></line>
		</svg>
	</button>
{/if}

<style>
	.poi-list-overlay {
		position: absolute;
		overflow: hidden;
		max-height: 25%;
		width: calc(100% - 20px);
		max-width: 1000px;
		bottom: 40px;
		left: 10px;
		right: 10px;
		background: rgba(250, 250, 250, 0.9);
		box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
		border-radius: 3px;
		border: 1px solid #999;
		font-family: Helvetica, '游ゴシック体', YuGothic, 'YuGothic M', sans-serif;
		display: flex;
		flex-direction: column;
	}

	.poi-list-overlay.large-screen {
		max-height: 70%;
		min-height: 18%;
		line-height: 21px;
		z-index: 4;
	}

	.poi-count {
		color: #e77;
		font-size: 14px;
		font-weight: bold;
		margin: 0 0 8px 0;
	}

	.poi-item {
		color: #333;
		text-decoration-color: #52c2d0;
		font-size: 13px;
		font-weight: normal;
		display: block;
		margin-bottom: 4px;
		line-height: 1.4;
	}

	.poi-item:hover {
		text-decoration: underline;
	}

	.poi-divider {
		border: none;
		border-top: 1px solid #ddd;
		margin: 4px 0;
	}

	.poi-list-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 20px;
		background: rgba(255, 255, 255, 0.95);
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
		flex-shrink: 0;
		border-radius: 3px 3px 0 0;
		gap: 12px;
		flex-wrap: wrap;
	}

	.poi-list-title-section {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.poi-list-title {
		color: #333;
		font-size: 14px;
		font-weight: 600;
		margin: 0;
	}

	.poi-count-badge {
		background-color: #52c2d0;
		color: white;
		font-size: 12px;
		font-weight: 600;
		padding: 3px 7px;
		border-radius: 50%;
		min-width: 22px;
		height: 22px;
		display: flex;
		align-items: center;
		justify-content: center;
		line-height: 1;
	}

	.poi-list-controls {
		display: flex;
		gap: 16px;
	}

	.sort-controls {
		display: flex;
		gap: 4px;
		align-items: center;
	}

	.sort-button {
		background: none;
		border: 1px solid rgba(0, 0, 0, 0.2);
		color: #666;
		cursor: pointer;
		padding: 6px;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		width: 32px;
		height: 32px;
	}

	.sort-button:hover {
		background-color: rgba(82, 194, 208, 0.1);
		border-color: #52c2d0;
		color: #52c2d0;
		transform: translateY(-1px);
	}

	.sort-button.active {
		background-color: #52c2d0;
		border-color: #52c2d0;
		color: white;
		box-shadow: 0 2px 4px rgba(82, 194, 208, 0.3);
	}

	.sort-button svg {
		width: 16px;
		height: 16px;
	}

	.poi-list-content {
		flex: 1;
		overflow-y: auto;
		padding: 8px 20px;
		line-height: 18px;
	}

	.expand-button,
	.collapse-button {
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 4px;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.expand-button:hover,
	.collapse-button:hover {
		background-color: rgba(0, 0, 0, 0.1);
		color: #333;
	}

	.expand-button svg,
	.collapse-button svg {
		width: 16px;
		height: 16px;
	}

	.show-list-button {
		position: fixed;
		bottom: 60px;
		left: 20px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(0, 0, 0, 0.5);
		border-radius: 8px;
		padding: 12px;
		width: 56px;
		height: 56px;
		color: #52c2d0;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		transition: all 0.2s ease;
		backdrop-filter: blur(10px);
		z-index: 20;
	}

	.show-list-button:hover {
		background: #52c2d0;
		color: white;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(82, 194, 208, 0.3);
	}

	.show-list-button svg {
		width: 20px;
		height: 20px;
	}
</style>
