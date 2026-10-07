import { expect, test } from '@playwright/test';

const categories = [
	{ id: 'cafe', label: 'カフェ' },
	{ id: 'ramen', label: 'ラーメン' },
	{ id: 'sushi', label: '寿司' },
	{ id: 'westernfood', label: '洋食' },
	{ id: 'izakaya', label: '居酒屋' },
	{ id: 'park', label: '公園' }
];

test('モバイルのメニューからカテゴリ一覧へ移動できる', async ({ page }) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await page.goto('/chiblo/');
	await expect(page.locator('.loading-screen')).toHaveCount(0, { timeout: 15_000 });
	await page.getByRole('button', { name: 'メニューを開く' }).click();

	await expect(page.getByRole('link', { name: 'カテゴリ別まとめを見る' })).toHaveAttribute(
		'href',
		'/chiblo/categories/'
	);
});

test('カテゴリ一覧から全カテゴリへ移動できる', async ({ page }) => {
	const response = await page.goto('/chiblo/categories/');

	expect(response?.status()).toBe(200);
	await expect(page.getByRole('heading', { level: 1 })).toHaveText(
		'東葛・TX沿線のカテゴリ別まとめ'
	);
	for (const category of categories) {
		const link = page.getByRole('link', { name: new RegExp(`^${category.label}`) });
		await expect(link).toHaveAttribute('href', `/chiblo/categories/${category.id}`);
		await expect(link.getByText(/\d+件/)).toBeVisible();
	}
});

for (const category of categories) {
	test(`${category.label}ページを表示できる`, async ({ page }) => {
		const response = await page.goto(`/chiblo/categories/${category.id}`);

		expect(response?.status()).toBe(200);
		await expect(page.getByRole('heading', { level: 1 })).toHaveText(
			`東葛・TX沿線の${category.label}まとめ`
		);
		await expect(page.getByText(/該当スポット: \d+件/)).toBeVisible();
		await expect(page.locator('ul > li').first()).toBeVisible();
	});
}

test('カテゴリページを下までスクロールできる', async ({ page }) => {
	await page.goto('/chiblo/categories/cafe');

	const main = page.locator('main');
	await main.evaluate((element) => element.scrollTo(0, element.scrollHeight));
	await expect.poll(() => main.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
});

test('カテゴリページから別のカテゴリへ移動できる', async ({ page }) => {
	await page.goto('/chiblo/categories/cafe');

	const navigation = page.getByRole('navigation', { name: 'カテゴリを切り替える' });
	await expect(navigation.getByText('カフェ', { exact: true })).toHaveAttribute(
		'aria-current',
		'page'
	);
	await expect(navigation.getByRole('link', { name: 'ラーメン' })).toHaveAttribute(
		'href',
		'/chiblo/categories/ramen'
	);
});

test('記事カードから地図の該当座標へリンクできる', async ({ page }) => {
	await page.goto('/chiblo/categories/cafe');

	const mapLink = page.getByRole('link', { name: '地図で見る' }).first();
	await expect(mapLink).toHaveAttribute('href', /^\/chiblo\/\?lat=[\d.]+&lng=[\d.]+&zoom=16$/);
});

test('カテゴリページの地図導線がトップページを指す', async ({ page }) => {
	await page.goto('/chiblo/categories/cafe');

	await expect(page.getByRole('link', { name: '地図トップ', exact: true })).toHaveAttribute(
		'href',
		'/chiblo/'
	);
});

test('存在しないカテゴリは404になる', async ({ page }) => {
	const response = await page.goto('/chiblo/categories/invalid');

	expect(response?.status()).toBe(404);
});
