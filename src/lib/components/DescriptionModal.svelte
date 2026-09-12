<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { base } from '$app/paths';
	import type { SiteInfo } from '$lib/types/poi';

	const dispatch = createEventDispatcher<{ close: void }>();

	export let showDescription = false;
	export let siteInfo: SiteInfo | null = null;

	function handleBackdropKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') dispatch('close');
	}
</script>

{#if showDescription}
	<div
		class="modal-backdrop"
		role="button"
		tabindex="0"
		on:click={() => dispatch('close')}
		on:keydown={handleBackdropKeydown}
	></div>
	<div class="description-overlay">
		<div class="description-content">
			<div class="description-header">
				<div class="title-with-logo">
					<img src="{base}/chiblogo.webp" alt="Chiblo Map" class="modal-logo" />
					<h2>ちーぶろマップ</h2>
				</div>
				<button
					type="button"
					class="close-button"
					on:click={() => dispatch('close')}
					aria-label="説明を閉じる"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>
			<p class="tipstyle01">
				東葛地域とつくばエクスプレス沿線を中心に、柏市・流山市・松戸市・野田市・我孫子市・守谷市とその周辺の地域ブロガーの方々が発信しているブログ記事を、地図上の場所とリンクさせて表示するマップです。
			</p>
			<p class="tipstyle01">
				地図上の水色の円をクリック/タップすると、その場所のお店やおすすめスポットのブログ記事が一覧で表示されます。
			</p>
			<p class="tipstyle01">
				ご意見等は<a href="https://form.run/@party--1681740493" target="_blank"
					>問い合わせフォーム（外部サービス）</a
				>からお知らせください。
			</p>

			{#if siteInfo}
				<hr class="section-divider" />

				<p class="info-item"><strong>記事データ更新日：</strong>{siteInfo.lastDataUpdate}</p>

				{#if siteInfo.announcements && siteInfo.announcements.length > 0}
					<div class="announcements">
						<p class="info-title"><strong>お知らせ</strong></p>
						{#each siteInfo.announcements as announcement (announcement.date + announcement.message)}
							<p class="announcement-item">• {announcement.message}</p>
						{/each}
					</div>
				{/if}

				<hr class="section-divider" />

				<p class="github-link">
					<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
					<a href={siteInfo.githubUrl} target="_blank" rel="external noopener noreferrer">
						View code on GitHub
					</a>
				</p>
			{/if}
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

	.description-overlay {
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

	.description-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 15px 15px 10px 15px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
		margin-bottom: 15px;
	}

	.description-content {
		padding: 0 15px 15px 15px;
	}

	.title-with-logo {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.modal-logo {
		width: 40px;
		height: 40px;
		border-radius: 8px;
		box-shadow: 0 4px 16px rgba(82, 194, 208, 0.2);
	}

	.description-content h2 {
		color: #2c3e50;
		font-size: 24px;
		font-weight: 600;
		margin: 0;
		letter-spacing: 0.5px;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
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

	.tipstyle01 {
		color: #2c3e50;
		font-size: 15px;
		font-weight: 400;
		line-height: 1.6;
		margin: 16px 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
		letter-spacing: 0.2px;
	}

	.tipstyle01 a {
		color: #3498db;
		text-decoration: underline;
	}

	.section-divider {
		border: none;
		border-top: 1px solid rgba(0, 0, 0, 0.1);
		margin: 16px 0;
	}

	.info-item {
		color: #2c3e50;
		font-size: 14px;
		font-weight: 500;
		line-height: 1.5;
		margin: 12px 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.announcements {
		margin: 16px 0;
	}

	.info-title {
		color: #2c3e50;
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 8px 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.announcement-item {
		color: #555;
		font-size: 13px;
		line-height: 1.5;
		margin: 4px 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.github-link {
		text-align: center;
		margin: 12px 0 8px 0;
	}

	.github-link a {
		color: #52c2d0;
		text-decoration: none;
		font-size: 13px;
		font-weight: 500;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
	}

	.github-link a:hover {
		text-decoration: underline;
	}
</style>
