import { expect, test, type Page } from '@playwright/test';

const savedState = {
	center: [140.02, 35.86],
	zoom: 13,
	filterKeyword: '',
	selectedPeriod: 0,
	selectedCategories: ['ramen'],
	showPOIList: true,
	isListExpanded: false,
	sortMode: 'name-asc'
};

async function seedMapState(page: Page) {
	await page.addInitScript((state) => {
		sessionStorage.setItem('chiblo-map-state', JSON.stringify(state));
	}, savedState);
}

test('保存済み状態がある場合は全画面ローディングを省略する', async ({ page }) => {
	await seedMapState(page);
	await page.goto('/chiblo/');

	await expect(page.locator('.loading-screen')).toHaveCount(0);
	await expect(page.locator('.maplibregl-map')).toBeVisible();
});

test('座標指定のURLで地図を開ける', async ({ page }) => {
	await page.goto('/chiblo/?lat=35.86&lng=140.02&zoom=16');

	await expect(page.locator('.maplibregl-map')).toBeVisible();
	await expect
		.poll(() =>
			page.evaluate(() => {
				const value = sessionStorage.getItem('chiblo-map-state');
				return value ? JSON.parse(value).center : null;
			})
		)
		.toEqual([expect.closeTo(140.02, 2), expect.closeTo(35.86, 2)]);
});

test('保存済みのカテゴリフィルターが復元される', async ({ page }) => {
	await seedMapState(page);
	await page.goto('/chiblo/');

	await expect
		.poll(() =>
			page.evaluate(() => {
				const value = sessionStorage.getItem('chiblo-map-state');
				return value ? JSON.parse(value).selectedCategories : [];
			})
		)
		.toEqual(['ramen']);
});
