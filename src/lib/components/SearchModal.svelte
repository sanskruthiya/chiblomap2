<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { StationOption } from '$lib/data/stations';

	const dispatch = createEventDispatcher<{
		close: void;
		getCurrentLocation: void;
		searchLocation: void;
		stationChange: string;
	}>();

	export let showLocationSearch = false;
	export let selectedStation = '';
	export let searchQuery = '';
	export let stationOptions: StationOption[] = [];

	function handleBackdropKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') dispatch('close');
	}
</script>

{#if showLocationSearch}
	<div
		class="modal-backdrop"
		role="button"
		tabindex="0"
		on:click={() => dispatch('close')}
		on:keydown={handleBackdropKeydown}
	></div>
	<div class="location-search-overlay">
		<div class="location-search-content">
			<div class="location-search-header">
				<h2>場所を調べる</h2>
				<button
					type="button"
					class="close-button"
					on:click={() => dispatch('close')}
					aria-label="場所検索を閉じる"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>

			<!-- 現在地を調べるボタン -->
			<div class="location-section">
				<h3>現在地を調べる</h3>
				<p class="section-description">あなたの現在地をマップに表示します</p>
				<button
					type="button"
					class="location-action-button current-location-btn"
					on:click={() => dispatch('getCurrentLocation')}
				>
					<svg
						class="button-icon"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"
						></path>
						<circle cx="12" cy="9" r="2.5"></circle>
					</svg>
					現在地を取得
				</button>
			</div>

			<!-- 場所を検索 -->
			<div class="location-section">
				<h3>場所を検索</h3>
				<p class="section-description">地名や住所を入力してマップに移動します</p>
				<div class="search-input-container">
					<input
						bind:value={searchQuery}
						type="text"
						placeholder="例：東京駅、柏市役所、千葉県松戸市"
						on:keydown={(e) => e.key === 'Enter' && dispatch('searchLocation')}
						class="search-input"
					/>
					<button
						type="button"
						class="location-action-button search-btn"
						on:click={() => dispatch('searchLocation')}
					>
						<svg
							class="button-icon"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
						>
							<circle cx="11" cy="11" r="8"></circle>
							<path d="m21 21-4.35-4.35"></path>
						</svg>
						検索
					</button>
				</div>
			</div>

			<!-- 駅名を選択 -->
			<div class="location-section">
				<h3>駅名を選択</h3>
				<p class="section-description">主要駅を選択してマップに移動します</p>
				<div class="station-select-container">
					<select
						bind:value={selectedStation}
						on:change={() => dispatch('stationChange', selectedStation)}
						class="station-select"
					>
						{#each stationOptions as station (station.id)}
							<option value={station.id}>{station.name}</option>
						{/each}
					</select>
				</div>
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

	.location-search-overlay {
		position: fixed;
		top: 40%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 500px;
		max-width: 90vw;
		max-height: 80vh;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #999;
		border-radius: 12px;
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

	.location-search-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 15px 15px 10px 15px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
		margin-bottom: 15px;
	}

	.location-search-content {
		padding: 0 15px 15px 15px;
	}

	.location-search-content h2 {
		color: #111;
		font-size: 18px;
		font-weight: normal;
		margin: 0;
		text-align: left;
	}

	.location-section {
		margin-bottom: 20px;
		padding-bottom: 15px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}

	.location-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
	}

	.location-section h3 {
		color: #333;
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 5px 0;
	}

	.section-description {
		color: #666;
		font-size: 12px;
		margin: 0 0 10px 0;
		line-height: 1.4;
	}

	.location-action-button {
		background-color: #52c2d0;
		color: white;
		border: none;
		border-radius: 6px;
		padding: 10px 16px;
		font-size: 13px;
		font-family: inherit;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 8px;
		transition: all 0.2s ease;
		width: 100%;
		justify-content: center;
	}

	.location-action-button:hover {
		background-color: #45a8b5;
		transform: translateY(-1px);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.location-action-button:active {
		transform: translateY(0);
	}

	.button-icon {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
	}

	.search-input-container {
		display: flex;
		gap: 8px;
		align-items: stretch;
	}

	.search-input {
		flex: 1;
		padding: 10px 12px;
		border: 1px solid #ccc;
		border-radius: 6px;
		font-size: 13px;
		font-family: inherit;
		background-color: white;
	}

	.search-input:focus {
		outline: none;
		border-color: #52c2d0;
		box-shadow: 0 0 0 2px rgba(82, 194, 208, 0.2);
	}

	.search-btn {
		flex-shrink: 0;
		width: auto;
		min-width: 80px;
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

	.station-select-container {
		margin-top: 10px;
	}

	.station-select {
		width: 100%;
		padding: 12px 16px;
		border: 1px solid #ccc;
		border-radius: 6px;
		font-size: 14px;
		font-family: inherit;
		background-color: white;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.station-select:focus {
		outline: none;
		border-color: #52c2d0;
		box-shadow: 0 0 0 2px rgba(82, 194, 208, 0.2);
	}

	.station-select:hover {
		border-color: #52c2d0;
	}
</style>
