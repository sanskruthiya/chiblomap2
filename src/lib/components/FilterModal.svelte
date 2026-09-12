<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { CategoryOption } from '$lib/data/categories';
	import type { PeriodOption } from '$lib/data/periods';

	const dispatch = createEventDispatcher<{
		close: void;
		applyFilter: void;
		selectPeriod: number;
		toggleCategory: string;
		clearFilter: void;
	}>();

	export let showFilter = false;
	export let filterKeyword = '';
	export let selectedPeriod = 0;
	export let selectedCategories: string[] = [];
	export let currentVisiblePOIs = 0;
	export let periodOptions: PeriodOption[] = [];
	export let categoryOptions: CategoryOption[] = [];

	function handleBackdropKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') dispatch('close');
	}
</script>

{#if showFilter}
	<div
		class="modal-backdrop"
		role="button"
		tabindex="0"
		on:click={() => dispatch('close')}
		on:keydown={handleBackdropKeydown}
	></div>
	<div class="filter-overlay">
		<div class="filter-overlay-inner">
			<div class="filter-header">
				<div class="filter-title-section">
					<h2>フィルター絞り込み</h2>
					<p class="filter-poi-count">現在表示中：{currentVisiblePOIs}件</p>
				</div>
				<button
					type="button"
					class="close-button"
					on:click={() => dispatch('close')}
					aria-label="フィルターを閉じる"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>

			<!-- 検索ワード入力 -->
			<div class="filter-section">
				<h3>検索ワード</h3>
				<p class="filter-description">店名、ブログ名、記事タイトルから検索</p>
				<div class="search-input-container">
					<input
						bind:value={filterKeyword}
						type="text"
						placeholder="例：カフェ、ラーメン、柏駅"
						on:input={() => dispatch('applyFilter')}
						class="filter-input"
					/>
				</div>
			</div>

			<!-- 期間フィルター -->
			<div class="filter-section">
				<h3>期間</h3>
				<p class="filter-description">記事の投稿時期で絞り込み</p>
				<div class="period-chips">
					{#each periodOptions as option (option.value)}
						<button
							type="button"
							class="chip"
							class:active={selectedPeriod === option.value}
							on:click={() => dispatch('selectPeriod', option.value)}
						>
							{option.label}
						</button>
					{/each}
				</div>
			</div>

			<!-- カテゴリフィルター -->
			<div class="filter-section">
				<h3>カテゴリ</h3>
				<p class="filter-description">店名・記事タイトルから絞り込み（複数選択可能）</p>
				<div class="category-chips">
					{#each categoryOptions as category (category.id)}
						<button
							type="button"
							class="chip"
							class:active={selectedCategories.includes(category.id)}
							on:click={() => dispatch('toggleCategory', category.id)}
						>
							{category.label}
						</button>
					{/each}
				</div>
			</div>

			<!-- リセットボタン -->
			<div class="filter-reset-section">
				<button type="button" class="filter-reset-button" on:click={() => dispatch('clearFilter')}>
					<svg
						class="reset-icon"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
						<path d="M21 3v5h-5"></path>
						<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
						<path d="M3 21v-5h5"></path>
					</svg>
					全ての条件をリセット
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 25;
		animation: backdropFadeIn 0.3s ease;
		cursor: pointer;
	}

	@keyframes backdropFadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.filter-overlay {
		position: fixed;
		top: 40%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 450px;
		max-width: 90vw;
		max-height: 80vh;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #999;
		border-radius: 12px;
		padding: 0;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
		z-index: 30;
		font-family: Helvetica, '游ゴシック体', YuGothic, 'YuGothic M', sans-serif;
		backdrop-filter: blur(10px);
		overflow-y: auto;
		animation: modalFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
	}

	@keyframes modalFadeIn {
		from {
			opacity: 0;
			transform: translate(-50%, -50%) scale(0.9);
		}
		to {
			opacity: 1;
			transform: translate(-50%, -50%) scale(1);
		}
	}

	.filter-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 20px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}

	.filter-title-section {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.filter-header h2 {
		color: #2c3e50;
		font-size: 22px;
		font-weight: 600;
		margin: 0;
		letter-spacing: 0.3px;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.filter-poi-count {
		color: #52c2d0;
		font-size: 15px;
		font-weight: 500;
		margin: 0;
		line-height: 1.2;
	}

	.filter-section {
		margin-bottom: 16px;
		padding: 0 20px 12px 20px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}

	.filter-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
	}

	.filter-section h3 {
		color: #2c3e50;
		font-size: 16px;
		font-weight: 600;
		margin: 0 0 6px 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.filter-description {
		color: #555;
		font-size: 14px;
		margin: 0 0 10px 0;
		line-height: 1.4;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.filter-input {
		flex: 1;
		padding: 10px 12px;
		border: 1px solid #ccc;
		border-radius: 6px;
		font-size: 13px;
		font-family: inherit;
		background-color: white;
	}

	.filter-input:focus {
		outline: none;
		border-color: #52c2d0;
		box-shadow: 0 0 0 2px rgba(82, 194, 208, 0.2);
	}

	.search-input-container {
		display: flex;
		gap: 8px;
		align-items: stretch;
	}

	.category-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 6px;
		line-height: 1.2;
	}

	.period-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 6px;
		line-height: 1.2;
	}

	.chip {
		background-color: rgba(255, 255, 255, 0.9);
		border: 1px solid #ddd;
		border-radius: 18px;
		padding: 5px 10px;
		font-size: 12px;
		font-family: inherit;
		font-weight: 600;
		color: #666;
		cursor: pointer;
		transition: all 0.2s ease;
		white-space: nowrap;
		user-select: none;
	}

	.chip:hover {
		background-color: rgba(82, 194, 208, 0.1);
		border-color: #52c2d0;
		color: #333;
	}

	.chip.active {
		background-color: #52c2d0;
		border-color: #52c2d0;
		color: white;
		box-shadow: 0 2px 4px rgba(82, 194, 208, 0.3);
	}

	.chip.active:hover {
		background-color: #45a8b5;
		border-color: #45a8b5;
	}

	.filter-reset-section {
		padding: 16px 20px;
		border-top: 1px solid rgba(0, 0, 0, 0.1);
		margin-top: 8px;
	}

	.filter-reset-button {
		width: 100%;
		background-color: #f8f9fa;
		border: 1px solid #dee2e6;
		border-radius: 8px;
		padding: 12px 16px;
		font-size: 14px;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
		font-weight: 500;
		color: #6c757d;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		transition: all 0.2s ease;
	}

	.filter-reset-button:hover {
		background-color: #e9ecef;
		border-color: #adb5bd;
		color: #495057;
		transform: translateY(-1px);
	}

	.filter-reset-button:active {
		transform: translateY(0);
		background-color: #dee2e6;
	}

	.reset-icon {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
	}

	.close-button {
		background: none;
		border: none;
		cursor: pointer;
		padding: 4px;
		border-radius: 4px;
		color: #666;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-button:hover {
		background-color: rgba(0, 0, 0, 0.1);
		color: #333;
	}

	.close-button svg {
		width: 20px;
		height: 20px;
	}
</style>
