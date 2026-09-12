<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{ toggle: void; menuAction: string }>();

	export let showMenu = false;
</script>

<div class="hamburger-container">
	<button
		type="button"
		class="hamburger-button"
		on:click={() => dispatch('toggle')}
		aria-expanded={showMenu}
		aria-label="メニューを開く"
	>
		<div class="hamburger-icon" class:active={showMenu}>
			<span></span>
			<span></span>
			<span></span>
		</div>
	</button>

	{#if showMenu}
		<div class="dropdown-menu">
			<button
				type="button"
				class="menu-item"
				on:click={() => dispatch('menuAction', 'description')}
			>
				<svg
					class="menu-icon"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<circle cx="12" cy="12" r="10"></circle>
					<path d="M9,9h6v6H9z"></path>
					<path d="M9 1v6M15 1v6M9 17v6M15 17v6M1 9h6M1 15h6M17 9h6M17 15h6"></path>
				</svg>
				このマップについて
			</button>
			<button type="button" class="menu-item" on:click={() => dispatch('menuAction', 'location')}>
				<svg
					class="menu-icon"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
					<circle cx="12" cy="10" r="3"></circle>
				</svg>
				場所を調べる
			</button>
			<button type="button" class="menu-item" on:click={() => dispatch('menuAction', 'filter')}>
				<svg
					class="menu-icon"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46 22,3"></polygon>
				</svg>
				フィルター絞り込み
			</button>
		</div>
	{/if}
</div>

<style>
	.hamburger-container {
		position: absolute;
		top: 16px;
		left: 16px;
		z-index: 30;
	}

	.hamburger-button {
		background-color: rgba(255, 255, 255, 0.95);
		border: 1px solid rgba(0, 0, 0, 0.5);
		border-radius: 8px;
		padding: 12px;
		cursor: pointer;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		transition: all 0.2s ease;
		backdrop-filter: blur(10px);
	}

	.hamburger-button:hover {
		background-color: rgba(255, 255, 255, 1);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
		transform: translateY(-1px);
	}

	.hamburger-icon {
		width: 24px;
		height: 18px;
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
	}

	.hamburger-icon span {
		display: block;
		height: 2px;
		width: 100%;
		background-color: #52c2d0;
		border-radius: 1px;
		transition: all 0.3s ease;
		transform-origin: center;
	}

	.hamburger-icon.active span:nth-child(1) {
		transform: rotate(45deg) translate(6px, 6px);
	}

	.hamburger-icon.active span:nth-child(2) {
		opacity: 0;
	}

	.hamburger-icon.active span:nth-child(3) {
		transform: rotate(-45deg) translate(6px, -6px);
	}

	.dropdown-menu {
		position: absolute;
		top: 60px;
		left: 0;
		background-color: rgba(255, 255, 255, 0.95);
		border-radius: 8px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
		backdrop-filter: blur(10px);
		min-width: 260px;
		overflow: hidden;
		animation: slideDown 0.2s ease;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.menu-item {
		width: 100%;
		background: none;
		border: none;
		padding: 14px 18px;
		text-align: left;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 14px;
		font-size: 16px;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
		font-weight: 500;
		color: #2c3e50;
		letter-spacing: 0.3px;
		transition: all 0.3s ease;
	}

	.menu-item:hover {
		background-color: rgba(52, 194, 208, 0.1);
		color: #1a252f;
		transform: translateX(2px);
		border-radius: 6px;
	}

	.menu-item:active {
		background-color: rgba(52, 194, 208, 0.2);
		transform: translateX(1px);
	}

	.menu-icon {
		width: 18px;
		height: 18px;
		color: #52c2d0;
		flex-shrink: 0;
	}
</style>
