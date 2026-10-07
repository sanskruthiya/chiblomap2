<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import maplibregl from 'maplibre-gl';
	import { deserialize } from 'flatgeobuf/lib/mjs/geojson.js';
	import { base } from '$app/paths';
	import HamburgerMenu from '$lib/components/HamburgerMenu.svelte';
	import POIList from '$lib/components/POIList.svelte';
	import DescriptionModal from '$lib/components/DescriptionModal.svelte';
	import SearchModal from '$lib/components/SearchModal.svelte';
	import FilterModal from '$lib/components/FilterModal.svelte';
	import { stationOptions } from '$lib/data/stations';
	import { categoryOptions } from '$lib/data/categories';
	import { loadMapState, saveMapState } from '$lib/data/mapState';
	import { periodOptions } from '$lib/data/periods';
	import type { POIFeature, SiteInfo } from '$lib/types/poi';
	import 'maplibre-gl/dist/maplibre-gl.css';

	const dispatch = createEventDispatcher();

	export let showInitially = true;

	let mapContainer: HTMLDivElement;
	let map: maplibregl.Map;
	let loadingProgress = 0;
	let isDataLoaded = false;
	let popup: maplibregl.Popup | null = null;
	let showPOIList = true;
	let isListExpanded = false;
	let centerPOIs: POIFeature[] = [];
	let showDescription = false;
	let showFilter = false;
	let filterKeyword = '';
	let showMenu = false;
	let showLocationSearch = false;
	let searchQuery = '';
	let selectedStation = ''; // 選択された駅
	let selectedPeriod = 0; // 0: 全期間, 1: 1ヶ月, 2: 3ヶ月, 3: 6ヶ月, 4: 1年
	let selectedCategories: string[] = []; // 選択されたカテゴリのリスト
	let initialCategoryFilterApplied = false; // カテゴリURLパラメータからの初期フィルター適用済みフラグ
	let sortMode = 'name-asc'; // ソートモード: 'name-asc'(デフォルト), 'date-desc'
	let totalPOICount = 0; // 実際のPOI総数（リアクティブ変数）
	let currentVisiblePOIs = 0; // 現在表示されているPOI数（フィルター適用後）
	let siteInfo: SiteInfo | null = null; // サイト情報（外部JSONから読み込み）
	let currentPopupFeatures: POIFeature[] = []; // 現在のポップアップに表示するPOI一覧
	let currentPopupIndex = 0; // カルーセルの現在のインデックス

	// 初期設定（旧バージョンから引用）
	const INITIAL_COORDS: [number, number] = [139.95, 35.89];
	const INITIAL_ZOOM = 11.5;
	const INITIAL_BEARING = 0;
	const INITIAL_PITCH = 0;

	function saveCurrentMapState() {
		if (!map) return;
		const center = map.getCenter();
		saveMapState({
			center: [center.lng, center.lat],
			zoom: map.getZoom(),
			filterKeyword,
			selectedPeriod,
			selectedCategories,
			showPOIList,
			isListExpanded,
			sortMode
		});
	}

	// POIデータを格納するオブジェクト
	const poiData: GeoJSON.FeatureCollection<GeoJSON.Point, Record<string, unknown>> = {
		type: 'FeatureCollection',
		features: []
	};

	// サイト情報の読み込み
	async function loadSiteInfo() {
		try {
			const response = await fetch(`${base}/data/site-info.json`, { cache: 'no-store' });
			if (!response.ok) throw new Error('サイト情報の取得に失敗しました');
			siteInfo = (await response.json()) as SiteInfo;
			return siteInfo;
		} catch (error) {
			console.error('サイト情報の読み込みに失敗しました:', error);
			// フォールバック用のデフォルト値
			siteInfo = {
				lastDataUpdate: '2025年12月15日',
				dataCount: 2568,
				announcements: [],
				githubUrl: 'https://github.com/sanskruthiya/chiblo-map'
			};
			return siteInfo;
		}
	}

	// FlatGeoBufデータの読み込み
	async function loadPOIData(lastDataUpdate?: string, dataCount?: number) {
		try {
			// lastDataUpdateとdataCountをキャッシュパラメータとして使用
			let cacheParam = 'default';
			if (lastDataUpdate) {
				// 日本語の日付を英数字のみのパラメータに変換し、件数を付加して同日更新にも対応
				cacheParam =
					lastDataUpdate.replace(/[年月日]/g, '').replace(/\s/g, '') +
					(dataCount ? `-${dataCount}` : '');
			}
			const url = `${base}/data/poi.fgb?v=${cacheParam}`;

			console.log('Loading POI data from:', url, 'Cache param:', cacheParam);

			const response = await fetch(url);
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			if (!response.body) {
				throw new Error('Response body is null');
			}

			let totalFeatures = 0;
			const iter = deserialize(response.body, undefined, (m: { featuresCount?: number }) => {
				totalFeatures = m?.featuresCount || 0;

				// メタデータ取得後に総件数を通知
				if (totalFeatures > 0) {
					dispatch('loadingProgress', {
						loadedCount: 0,
						totalCount: totalFeatures
					});
				}
			});

			for await (const feature of iter) {
				poiData.features.push(
					feature as unknown as GeoJSON.Feature<GeoJSON.Point, Record<string, unknown>>
				);

				// 総件数が分かっている場合のみ進捗計算
				if (totalFeatures > 0) {
					loadingProgress = Math.floor((poiData.features.length / totalFeatures) * 100);

					// 進捗を親コンポーネントに通知
					dispatch('loadingProgress', {
						loadedCount: poiData.features.length,
						totalCount: totalFeatures
					});
				}

				// 進捗更新（256件ごとまたは完了時）
				if (
					(totalFeatures > 0 && poiData.features.length === totalFeatures) ||
					poiData.features.length % 256 === 0
				) {
					updateMapData();
				}
			}

			isDataLoaded = true;
			currentVisiblePOIs = poiData.features.length; // 初期状態では全POIが表示
			console.log(`Loaded ${poiData.features.length} POI features`);

			// featuresCountが取得できなかった場合も完了を通知
			if (totalFeatures === 0 && poiData.features.length > 0) {
				dispatch('loadingProgress', {
					loadedCount: poiData.features.length,
					totalCount: poiData.features.length
				});
			}
		} catch (error) {
			console.error('POIデータの読み込みに失敗しました:', error);

			// エラー時もローディング完了として扱い、空のデータでマップを表示
			isDataLoaded = true;

			// エラー情報を親コンポーネントに通知
			const errorMessage =
				error instanceof Error ? error.message : 'データの読み込みに失敗しました';
			dispatch('loadingProgress', {
				loadedCount: 0,
				totalCount: 0,
				error: errorMessage
			});
		}
	}

	// マップデータの更新
	function updateMapData() {
		if (!map) return;

		const source = map.getSource('poi-data') as maplibregl.GeoJSONSource;
		if (source) {
			source.setData(poiData);
		}
	}

	// カルーセル型ポップアップHTML作成
	function createMultiPOIPopupHTML(features: POIFeature[]): string {
		// 状態を更新
		currentPopupFeatures = features;
		currentPopupIndex = 0;

		// リンクタイプの取得
		const getLinkType = (flag: string) => {
			const types: { [key: string]: string } = {
				'1': '公式サイト',
				'2': 'Instagram',
				'3': 'Twitter'
			};
			return types[flag] || 'リンク';
		};

		// 単一カード生成関数
		const createSingleCard = (feat: POIFeature) => {
			const properties = feat.properties;
			const geometry = feat.geometry;
			const coordinates = geometry?.coordinates || [0, 0];

			const name = properties.name_poi || '名前不明';
			const blogSource = properties.blog_source || '';
			const titleSource = properties.title_source || '';
			const linkSource = properties.link_source || '';
			const dateText = properties.date_text || '';
			const urlFlag = properties.url_flag || '0';
			const urlLink = properties.url_link || '';

			let cardContent = `
				<div class="poi-card">
					<div class="poi-header">
						<div class="poi-icon">📍</div>
						<h3 class="poi-name">${name}</h3>
					</div>
					
					<div class="poi-links">`;

			// 公式リンク
			if (urlFlag !== '0' && urlLink) {
				cardContent += `
					<a href="${urlLink}" target="_blank" rel="noopener" class="poi-link official-link">
						<span class="link-icon">🏠</span>
						<span class="link-text">${getLinkType(urlFlag)}</span>
					</a>`;
			}

			// Google Mapリンク
			cardContent += `
				<a href="https://www.google.com/maps/search/?api=1&query=${coordinates[1].toFixed(5)},${coordinates[0].toFixed(5)}&zoom=18" target="_blank" rel="noopener" class="poi-link map-link">
					<span class="link-icon">🗺️</span>
					<span class="link-text">Google Map</span>
				</a>
			</div>
			
			<div class="blog-section">
				<div class="blog-meta">
					<span class="blog-icon">📝</span>
					<span class="blog-date">${dateText}</span>
					<span class="blog-source">${blogSource}</span>
				</div>
				<div class="blog-title">${linkSource ? `<a href="${linkSource}" target="_blank" rel="noopener" class="blog-title-link">${titleSource}</a>` : titleSource}</div>`;

			cardContent += `
				</div>
			</div>`;

			return cardContent;
		};

		// カルーセルコンテナの作成
		let popupContent = '<div class="carousel-popup-container">';

		// ヘッダー（カウンターとナビゲーション）
		if (features.length > 1) {
			popupContent += `
				<div class="carousel-header">
					<button class="carousel-nav carousel-prev" onclick="window.navigatePopup(-1)" ${features.length <= 1 ? 'disabled' : ''}>
						<span>←</span>
					</button>
					<div class="carousel-counter">
						<span class="current-index">1</span>/<span class="total-count">${features.length}</span>
					</div>
					<button class="carousel-nav carousel-next" onclick="window.navigatePopup(1)" ${features.length <= 1 ? 'disabled' : ''}>
						<span>→</span>
					</button>
				</div>`;
		}

		// カルーセルコンテンツ
		popupContent += '<div class="carousel-content">';
		features.forEach((feat, index) => {
			popupContent += `<div class="carousel-slide ${index === 0 ? 'active' : ''}" data-index="${index}">`;
			popupContent += createSingleCard(feat);
			popupContent += '</div>';
		});
		popupContent += '</div>';

		popupContent += '</div>';
		return popupContent;
	}

	// カルーセルナビゲーション関数
	function navigatePopup(direction: number) {
		if (currentPopupFeatures.length <= 1) return;

		const newIndex = currentPopupIndex + direction;
		if (newIndex < 0 || newIndex >= currentPopupFeatures.length) return;

		currentPopupIndex = newIndex;

		// DOM更新
		const slides = document.querySelectorAll('.carousel-slide');
		const counter = document.querySelector('.current-index');
		const prevBtn = document.querySelector('.carousel-prev') as HTMLButtonElement;
		const nextBtn = document.querySelector('.carousel-next') as HTMLButtonElement;

		slides.forEach((slide, index) => {
			slide.classList.toggle('active', index === currentPopupIndex);
		});

		if (counter) {
			counter.textContent = (currentPopupIndex + 1).toString();
		}

		// ボタンの有効/無効状態
		if (prevBtn) prevBtn.disabled = currentPopupIndex === 0;
		if (nextBtn) nextBtn.disabled = currentPopupIndex === currentPopupFeatures.length - 1;
	}

	// キーボードイベントの追加
	function addPopupKeyboardEvents() {
		const handleKeydown = (e: KeyboardEvent) => {
			if (!popup || currentPopupFeatures.length <= 1) return;

			switch (e.key) {
				case 'ArrowLeft':
				case 'ArrowUp':
					e.preventDefault();
					navigatePopup(-1);
					break;
				case 'ArrowRight':
				case 'ArrowDown':
					e.preventDefault();
					navigatePopup(1);
					break;
				case 'Escape':
					e.preventDefault();
					if (popup) popup.remove();
					break;
			}
		};

		// イベントリスナーを追加
		document.addEventListener('keydown', handleKeydown);

		// ポップアップが閉じられた時にイベントリスナーを削除
		if (popup) {
			popup.on('close', () => {
				document.removeEventListener('keydown', handleKeydown);
			});
		}
	}

	// POI配列をソートする関数
	function sortPOIs(pois: POIFeature[]): POIFeature[] {
		if (sortMode === 'date-desc') {
			// 日付の新しい順（date_stampの降順）
			return [...pois].sort((a, b) => {
				const dateA = a.properties?.date_stamp || 0;
				const dateB = b.properties?.date_stamp || 0;
				return dateB - dateA;
			});
		}
		// デフォルト: 場所名の昇順（name_poiのあいうえお順）
		return [...pois].sort((a, b) => {
			const nameA = a.properties?.name_poi || '';
			const nameB = b.properties?.name_poi || '';
			return nameA.localeCompare(nameB, 'ja');
		});
	}

	// ソートモードを変更する関数
	function changeSortMode(mode: string) {
		sortMode = mode;
		updateCenterPOIs(); // リストを再更新
		saveCurrentMapState();
	}

	// マップ中央付近のPOIを取得する関数（旧バージョン準拠）
	function updateCenterPOIs() {
		if (!map || !isDataLoaded) return;

		const center = map.getCenter();
		const point = map.project(center);
		const bbox: [maplibregl.PointLike, maplibregl.PointLike] = [
			[point.x - 30, point.y - 30], // 左上
			[point.x + 30, point.y + 30] // 右下
		];

		// 旧バージョンと同じピクセルベースの矩形範囲でPOIを取得
		const features = map.queryRenderedFeatures(bbox, {
			layers: ['poi-points']
		});

		totalPOICount = features.length; // 実際の総数を保存
		const limitedFeatures = features.slice(0, 99) as unknown as POIFeature[]; // 最大99件に制限
		centerPOIs = sortPOIs(limitedFeatures); // ソートを適用
	}

	// 期間フィルターの日付計算
	function getPeriodTimestamp(days: number | null): number {
		if (days === null) return 0; // 全期間

		const now = new Date();
		const pastDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
		return Math.floor(pastDate.getTime() / 1000); // UNIXタイムスタンプ（秒）
	}

	// 期間選択の処理
	function selectPeriod(periodValue: number) {
		selectedPeriod = periodValue;
		applyFilter();
	}

	// カテゴリ選択の処理（複数選択対応）
	function toggleCategory(categoryId: string) {
		if (selectedCategories.includes(categoryId)) {
			selectedCategories = selectedCategories.filter((id) => id !== categoryId);
		} else {
			selectedCategories = [...selectedCategories, categoryId];
		}
		applyFilter();
	}

	// フィルター適用
	function applyFilter() {
		if (!map || !isDataLoaded) return;

		// 検索ワード、期間、カテゴリのいずれかが設定されている場合
		if (filterKeyword.trim().length > 0 || selectedPeriod > 0 || selectedCategories.length > 0) {
			applyCombinedFilter();
		} else {
			clearAllFilters();
		}

		// POIリストも更新
		updateCenterPOIs();
		saveCurrentMapState();
	}

	// 検索ワード + 期間 + カテゴリの複合フィルター
	function applyCombinedFilter() {
		const keyword = filterKeyword.toLowerCase().trim();
		const selectedOption = periodOptions.find((opt) => opt.value === selectedPeriod);
		const periodTimestamp = selectedOption ? getPeriodTimestamp(selectedOption.days) : 0;

		// 選択されたカテゴリのキーワードを収集
		const categoryKeywords: string[] = [];
		selectedCategories.forEach((categoryId) => {
			const category = categoryOptions.find((cat) => cat.id === categoryId);
			if (category) {
				categoryKeywords.push(...category.keywords);
			}
		});

		// 全POIから条件に一致するものを抽出
		const matchingFeatures = poiData.features.filter((feature) => {
			const props = feature.properties as unknown as POIFeature['properties'] | undefined;
			if (!props) return false;

			// 期間フィルター
			if (selectedPeriod > 0) {
				const featureTimestamp = props.date_stamp || 0;
				if (featureTimestamp < periodTimestamp) return false;
			}

			// 検索ワードフィルター
			if (keyword.length > 0) {
				const searchTargets = [
					props.name_poi || '',
					props.flag_poi || '',
					props.blog_source || '',
					props.title_source || ''
				];

				const matchesKeyword = searchTargets.some((target) =>
					target.toLowerCase().includes(keyword)
				);

				if (!matchesKeyword) return false;
			}

			// カテゴリフィルター（name_poiとtitle_sourceのみを対象）
			if (categoryKeywords.length > 0) {
				const categoryTargets = [props.name_poi || '', props.title_source || ''];

				const matchesCategory = categoryKeywords.some((categoryKeyword) =>
					categoryTargets.some((target) =>
						target.toLowerCase().includes(categoryKeyword.toLowerCase())
					)
				);

				if (!matchesCategory) return false;
			}

			return true;
		});

		if (matchingFeatures.length > 0) {
			// 一致するPOIのfidリストを作成
			const matchingFids = matchingFeatures
				.map((feature) => (feature.properties as unknown as POIFeature['properties']).fid)
				.filter((fid) => fid !== undefined);

			// MapLibre GL JSのフィルター式を作成
			const filterExpression: maplibregl.FilterSpecification = [
				'match',
				['get', 'fid'],
				matchingFids,
				true,
				false
			];

			// 各レイヤーにフィルターを適用
			map.setFilter('poi-points', filterExpression);
			map.setFilter('poi-heat', filterExpression);
			map.setFilter('poi-text', filterExpression);
		} else {
			// 検索結果が0件の場合、全てのPOIを非表示
			const noResultFilter: maplibregl.FilterSpecification = ['has', 'poi_nonexistent'];
			map.setFilter('poi-points', noResultFilter);
			map.setFilter('poi-heat', noResultFilter);
			map.setFilter('poi-text', noResultFilter);
		}

		// 現在表示されているPOI数を更新
		currentVisiblePOIs = matchingFeatures.length;
	}

	// 全フィルターをクリア
	function clearAllFilters() {
		if (!map) return;

		// 全レイヤーのフィルターを削除
		map.setFilter('poi-points', null);
		map.setFilter('poi-heat', null);
		map.setFilter('poi-text', null);
	}

	// フィルタークリア
	function clearFilter() {
		filterKeyword = '';
		selectedPeriod = 0;
		selectedCategories = [];

		// 全てのフィルターをクリア
		if (map && isDataLoaded) {
			map.setFilter('poi-points', null);
			map.setFilter('poi-heat', null);
			map.setFilter('poi-text', null);

			// 現在表示されているPOI数を全件に戻す
			currentVisiblePOIs = poiData.features.length;
		}
		saveCurrentMapState();
	}

	// 現在地を取得
	function getCurrentLocation() {
		if (!navigator.geolocation) {
			alert('お使いのブラウザは位置情報に対応していません。');
			return;
		}

		navigator.geolocation.getCurrentPosition(
			(position) => {
				const { latitude, longitude } = position.coords;
				map.flyTo({
					center: [longitude, latitude],
					zoom: 15,
					duration: 2000
				});
			},
			(error) => {
				console.error('位置情報の取得に失敗しました:', error);
				alert('位置情報の取得に失敗しました。位置情報の使用を許可してください。');
			}
		);
	}

	// URLのstationパラメータを更新する関数
	function updateStationParam(stationId: string) {
		const url = new URL(window.location.href);
		if (stationId) {
			url.searchParams.set('station', stationId);
		} else {
			url.searchParams.delete('station');
		}
		window.history.replaceState({}, '', url.toString());
	}

	// 駅を選択して移動する関数
	function selectStation() {
		if (!selectedStation) {
			return;
		}

		const station = stationOptions.find((s) => s.id === selectedStation);
		if (station && station.lat && station.lng) {
			map.flyTo({
				center: [station.lng, station.lat],
				zoom: 15,
				duration: 2000
			});

			// URLパラメータを更新
			updateStationParam(station.id);

			// 選択成功後にモーダルを閉じる
			showLocationSearch = false;
			selectedStation = '';
		}
	}

	// 場所を検索する関数
	async function searchLocation() {
		if (!searchQuery.trim()) {
			alert('検索する場所を入力してください。');
			return;
		}

		try {
			// Nominatim API（OpenStreetMap）を使用した地名検索
			const response = await fetch(
				`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=5&countrycodes=jp`
			);
			const results = await response.json();

			if (results.length > 0) {
				const result = results[0];
				const lat = parseFloat(result.lat);
				const lon = parseFloat(result.lon);

				map.flyTo({
					center: [lon, lat],
					zoom: 15,
					duration: 2000
				});

				// 検索成功後にモーダルを閉じる
				showLocationSearch = false;
				searchQuery = '';
			} else {
				alert('指定された場所が見つかりませんでした。別の検索語句をお試しください。');
			}
		} catch (error) {
			console.error('場所検索エラー:', error);
			alert('場所検索中にエラーが発生しました。');
		}
	}

	// メニュー項目選択時の処理
	function handleMenuAction(action: string) {
		switch (action) {
			case 'description':
				showDescription = true;
				break;
			case 'location':
				showLocationSearch = true;
				break;
			case 'filter':
				showFilter = true;
				break;
		}
		showMenu = false; // メニューを閉じる
	}

	onMount(() => {
		// サイト情報を読み込んでからマップを初期化
		loadSiteInfo().then((siteData) => {
			// グローバル関数として登録
			(window as unknown as Record<string, unknown>).navigatePopup = navigatePopup;

			// URLクエリパラメータから初期表示駅を取得
			const urlParams = new URLSearchParams(window.location.search);
			const stationParam = urlParams.get('station');
			const savedState = loadMapState();
			let initCenter: [number, number] = savedState?.center ?? INITIAL_COORDS;
			let initZoom = savedState?.zoom ?? INITIAL_ZOOM;

			if (savedState) {
				filterKeyword = savedState.filterKeyword;
				selectedPeriod = savedState.selectedPeriod;
				selectedCategories = savedState.selectedCategories.filter((id) =>
					categoryOptions.some((category) => category.id === id)
				);
				showPOIList = savedState.showPOIList;
				isListExpanded = savedState.isListExpanded;
				sortMode = savedState.sortMode;
			}

			if (stationParam) {
				const matchedStation = stationOptions.find((s) => s.id === stationParam);
				if (matchedStation && matchedStation.lat && matchedStation.lng) {
					initCenter = [matchedStation.lng, matchedStation.lat];
					initZoom = 14;
				}
			}

			// 記事カード等からの座標指定を最優先で適用
			const latParam = urlParams.get('lat');
			const lngParam = urlParams.get('lng');
			const zoomParam = urlParams.get('zoom');
			if (latParam !== null && lngParam !== null) {
				const lat = Number(latParam);
				const lng = Number(lngParam);
				const zoom = zoomParam === null ? NaN : Number(zoomParam);
				if (Number.isFinite(lat) && Number.isFinite(lng)) {
					initCenter = [lng, lat];
					if (Number.isFinite(zoom)) {
						initZoom = Math.min(Math.max(zoom, 8), 18);
					}
				}
			}

			// MapLibre GL JSマップの初期化
			map = new maplibregl.Map({
				container: mapContainer,
				style: `${base}/data/basemap_style.json`,
				center: initCenter,
				zoom: initZoom,
				bearing: INITIAL_BEARING,
				pitch: INITIAL_PITCH,
				maxZoom: 18,
				minZoom: 8
			});

			// マップの読み込み完了時の処理
			map.on('load', () => {
				console.log('Map loaded successfully');

				// basemap_style.json の center/zoom がコンストラクタ指定を上書きするため、
				// スタイル適用後に初期表示位置を設定し直す
				map.jumpTo({ center: initCenter, zoom: initZoom });

				// POIデータソースを追加
				map.addSource('poi-data', {
					type: 'geojson',
					data: poiData
				});

				// POI疑似レイヤー（透明、クエリ用）
				map.addLayer({
					id: 'poi-pseudo',
					type: 'circle',
					source: 'poi-data',
					minzoom: 5,
					layout: {
						visibility: 'visible'
					},
					paint: {
						'circle-color': 'transparent',
						'circle-stroke-color': 'transparent'
					}
				});

				// POIポイントレイヤー（旧バージョン準拠）
				map.addLayer({
					id: 'poi-points',
					type: 'circle',
					source: 'poi-data',
					minzoom: 5,
					layout: {
						visibility: 'visible'
					},
					paint: {
						'circle-color': 'transparent',
						'circle-blur': 0.1,
						'circle-stroke-color': '#00bfff',
						'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 5, 1, 12, 1, 20, 3],
						'circle-stroke-opacity': ['interpolate', ['linear'], ['zoom'], 12, 0.2, 18, 1],
						'circle-opacity': 0.1,
						'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 4, 20, 12]
					}
				});

				// POIヒートマップレイヤー（水玉模様）
				map.addLayer({
					id: 'poi-heat',
					type: 'heatmap',
					source: 'poi-data',
					minzoom: 5,
					paint: {
						'heatmap-weight': ['interpolate', ['linear'], ['get', 'count'], 1, 1, 10, 50],
						'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 5, 1, 20, 20],
						'heatmap-color': [
							'interpolate',
							['linear'],
							['heatmap-density'],
							0,
							'rgba(200,255,255,0)',
							0.4,
							'#e0ffff',
							1,
							'#00bfff'
						],
						'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 1, 20, 15],
						'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 5, 1, 12, 0.6, 20, 0]
					},
					layout: {
						visibility: 'visible'
					}
				});

				// POIテキストレイヤー（旧バージョン準拠）
				map.addLayer({
					id: 'poi-text',
					type: 'symbol',
					source: 'poi-data',
					minzoom: 8,
					layout: {
						'text-field': ['get', 'name_poi'],
						'text-offset': [0, 0],
						'text-anchor': 'top',
						'icon-image': '',
						'symbol-sort-key': ['get', 'date_stamp'],
						'symbol-z-order': 'viewport-y',
						'text-allow-overlap': false,
						'text-ignore-placement': false,
						'text-size': ['interpolate', ['linear'], ['zoom'], 8, 10, 12, 10, 20, 12],
						'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold']
					},
					paint: {
						'text-color': '#333',
						'text-halo-color': '#fff',
						'text-halo-width': 1
					}
				});

				// データ読み込み開始（サイト情報のlastDataUpdateを使用）
				loadPOIData(siteData?.lastDataUpdate, siteData?.dataCount);

				// データ読み込み完了時にPOIリストを初期表示
				map.on('sourcedata', (e) => {
					if (e.sourceId === 'poi-data' && e.isSourceLoaded && isDataLoaded) {
						updateCenterPOIs();

						// URLパラメータからのカテゴリー初期フィルターを適用
						if (
							!initialCategoryFilterApplied &&
							(filterKeyword.trim().length > 0 ||
								selectedPeriod > 0 ||
								selectedCategories.length > 0)
						) {
							applyFilter();
							initialCategoryFilterApplied = true;
						}
					}
				});

				// POIクリックイベントを追加（複数POI対応）
				map.on('click', 'poi-points', (e) => {
					// 既存のポップアップを削除
					if (popup) {
						popup.remove();
					}

					// クリックした位置の全てのPOIを取得
					const features = map.queryRenderedFeatures(e.point, { layers: ['poi-points'] });

					if (features.length > 0) {
						// マップの中央をクリックした位置に移動
						map.easeTo({ center: e.lngLat, duration: 500 });

						// ポップアップを作成して表示
						popup = new maplibregl.Popup({
							closeButton: true,
							closeOnClick: true,
							anchor: 'bottom',
							maxWidth: '360px',
							className: 'scrollable-popup'
						})
							.setLngLat(e.lngLat)
							.setHTML(createMultiPOIPopupHTML(features as unknown as POIFeature[]))
							.addTo(map);
						addPopupKeyboardEvents();
						updateCenterPOIs();
					}
				});

				// マウスカーソルの変更
				map.on('mouseenter', 'poi-points', () => {
					map.getCanvas().style.cursor = 'pointer';
				});

				map.on('mouseleave', 'poi-points', () => {
					map.getCanvas().style.cursor = '';
				});

				// ナビゲーションコントロールを追加（方位アイコンを非表示）
				map.addControl(
					new maplibregl.NavigationControl({
						showCompass: false
					}),
					'top-right'
				);

				// ジオロケーションコントロールを追加
				map.addControl(
					new maplibregl.GeolocateControl({
						positionOptions: {
							enableHighAccuracy: true
						},
						trackUserLocation: true
					}),
					'top-right'
				);

				// マップ移動時にPOIリストを更新
				map.on('moveend', () => {
					if (showPOIList) {
						updateCenterPOIs();
					}
					saveCurrentMapState();
				});

				// 初期POIリスト表示
				if (isDataLoaded) {
					updateCenterPOIs();
				}

				saveCurrentMapState();
			});
		});

		// クリーンアップ関数
		return () => {
			saveCurrentMapState();
			map?.remove();
		};
	});
</script>

<div class="relative h-full w-full">
	<!-- マップコンテナ -->
	<div bind:this={mapContainer} class="h-full w-full"></div>

	<!-- ローディング表示（showInitiallyがfalseの場合は非表示） -->
	{#if !isDataLoaded && showInitially}
		<div class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-10">
			<div class="text-center">
				<div
					class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"
				></div>
				<p class="text-lg font-medium text-gray-700">POIデータを読み込み中...</p>
				<p class="text-sm text-gray-500">{loadingProgress}% 完了</p>
			</div>
		</div>
	{/if}

	<!-- ハンバーガーメニュー -->
	<HamburgerMenu
		{showMenu}
		on:toggle={() => (showMenu = !showMenu)}
		on:menuAction={(e) => handleMenuAction(e.detail)}
	/>

	<!-- 画面中央の十字アイコン（検索範囲表示） -->
	<div class="crosshair">
		<svg
			focusable="false"
			width="100px"
			height="100px"
			viewBox="-0.5 0 25 25"
			fill="none"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				d="M21.5001 12.5H16.5601"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M7.44 12.5H2.5"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M12 22V17.06"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M12 7.94V3"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M5.26001 10.5C5.93001 8.22 7.73001 6.41999 10.01 5.75999"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M14.01 19.24C16.29 18.58 18.09 16.78 18.76 14.5"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M5.26001 14.5C5.93001 16.78 7.73001 18.58 10.01 19.24"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<path
				d="M14.01 5.75999C16.29 6.41999 18.09 8.22 18.76 10.5"
				stroke="rgba(100,100,100,0.5)"
				stroke-miterlimit="10"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
		</svg>
	</div>

	<!-- POIリスト表示 -->
	<POIList
		{showPOIList}
		{isListExpanded}
		{totalPOICount}
		{centerPOIs}
		{sortMode}
		on:toggle={() => {
			showPOIList = !showPOIList;
			if (showPOIList) updateCenterPOIs();
		}}
		on:toggleSize={() => (isListExpanded = !isListExpanded)}
		on:changeSort={(e) => changeSortMode(e.detail)}
	/>

	<!-- 説明オーバーレイ -->
	<DescriptionModal {showDescription} {siteInfo} on:close={() => (showDescription = false)} />

	<!-- 場所検索モーダル -->
	<SearchModal
		{showLocationSearch}
		bind:selectedStation
		bind:searchQuery
		{stationOptions}
		on:close={() => (showLocationSearch = false)}
		on:getCurrentLocation={getCurrentLocation}
		on:searchLocation={searchLocation}
		on:stationChange={() => selectStation()}
	/>

	<!-- フィルターオーバーレイ -->
	<FilterModal
		{showFilter}
		bind:filterKeyword
		bind:selectedPeriod
		bind:selectedCategories
		{currentVisiblePOIs}
		{periodOptions}
		{categoryOptions}
		on:close={() => (showFilter = false)}
		on:applyFilter={applyFilter}
		on:selectPeriod={(e) => selectPeriod(e.detail)}
		on:toggleCategory={(e) => toggleCategory(e.detail)}
		on:clearFilter={clearFilter}
	/>
</div>

<style>
	/* MapLibre GL JSのスタイルを確実に適用 */
	:global(.maplibregl-map) {
		font-family: inherit;
	}

	/* 旧バージョン準拠のポップアップスタイル */
	:global(.scrollable-popup .maplibregl-popup-content) {
		background: #fff;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
		padding: 4px 5px;
		overflow-y: scroll !important;
		max-height: 240px;
		z-index: 2;
	}

	/* 旧バージョンのテーブルスタイル */
	:global(.scrollable-popup table) {
		table-layout: auto;
		width: 100%;
		border-collapse: collapse;
		border-spacing: 1px;
		border: 1px solid #999;
	}

	:global(.scrollable-popup table.tablestyle02 th) {
		color: #fff;
		background-color: #52c2d0;
		text-align: center;
		padding: 2px;
		font-size: 13px;
		font-weight: 400;
		font-family: Helvetica, '游ゴシック体', YuGothic, 'YuGothic M', sans-serif;
	}

	:global(.scrollable-popup table.tablestyle02 th.main) {
		font-weight: 600;
		width: 360px;
		text-align: center;
	}

	:global(.scrollable-popup table.tablestyle02 td) {
		color: #333;
		background-color: #fff;
		height: 50px;
		padding: 2px;
	}

	:global(.scrollable-popup table.tablestyle02 td.main) {
		text-align: left;
		line-height: 22px;
		font-size: 13px;
		font-weight: 400;
		font-family: Helvetica, '游ゴシック体', YuGothic, 'YuGothic M', sans-serif;
	}

	:global(.scrollable-popup table.tablestyle02 td.main summary) {
		font-size: 14px;
	}

	:global(.scrollable-popup table.tablestyle02 tr:nth-child(odd) td) {
		background-color: #eee;
	}

	/* スクロールバーのスタイリング */
	:global(.scrollable-popup .maplibregl-popup-content::-webkit-scrollbar) {
		width: 6px;
	}

	:global(.scrollable-popup .maplibregl-popup-content::-webkit-scrollbar-track) {
		background: #f1f1f1;
		border-radius: 3px;
	}

	:global(.scrollable-popup .maplibregl-popup-content::-webkit-scrollbar-thumb) {
		background: #c1c1c1;
		border-radius: 3px;
	}

	:global(.scrollable-popup .maplibregl-popup-content::-webkit-scrollbar-thumb:hover) {
		background: #a8a8a8;
	}

	/* 画面中央の十字アイコンのスタイル（旧バージョン準拠） */
	.crosshair {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		pointer-events: none;
		z-index: 1;
	}

	/* カード型ポップアップのスタイル */
	:global(.popup-container) {
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
		max-width: 320px;
		min-width: 280px;
	}

	:global(.poi-card) {
		background: #fff;
		border-radius: 12px;
		padding: 16px;
		margin-bottom: 0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	:global(.poi-card-separator) {
		margin-top: 12px;
		border-top: 1px solid #e0e0e0;
		padding-top: 16px;
	}

	:global(.poi-header) {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 8px;
	}

	:global(.poi-icon) {
		font-size: 16px;
		line-height: 1;
	}

	:global(.poi-name) {
		font-size: 15px;
		font-weight: 600;
		color: #2c3e50;
		margin: 0;
		line-height: 1.2;
	}

	:global(.poi-links) {
		display: flex;
		gap: 6px;
		margin-bottom: 8px;
		flex-wrap: wrap;
	}

	:global(.poi-link) {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 6px 10px;
		background: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 6px;
		text-decoration: none;
		font-size: 12px;
		font-weight: 500;
		color: #495057;
		transition: all 0.2s ease;
	}

	:global(.poi-link:hover) {
		background: #52c2d0;
		border-color: #52c2d0;
		color: white;
		transform: translateY(-1px);
	}

	:global(.link-icon) {
		font-size: 14px;
		line-height: 1;
	}

	:global(.link-text) {
		white-space: nowrap;
	}

	:global(.blog-section) {
		border-top: 1px solid #f0f0f0;
		padding-top: 8px;
	}

	:global(.blog-meta) {
		display: flex;
		align-items: center;
		gap: 5px;
		margin-bottom: 6px;
		font-size: 11px;
		color: #6c757d;
	}

	:global(.blog-icon) {
		font-size: 12px;
		line-height: 1;
	}

	:global(.blog-date) {
		font-weight: 500;
	}

	:global(.blog-source) {
		font-weight: 500;
		color: #52c2d0;
	}

	:global(.blog-title) {
		font-size: 14px;
		font-weight: 500;
		color: #2c3e50;
		line-height: 1.3;
		margin-bottom: 0;
		min-height: 60px;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	:global(.blog-title-link) {
		color: #2c3e50;
		text-decoration: none;
		transition: color 0.2s ease;
	}

	:global(.blog-title-link:hover) {
		color: #52c2d0;
		text-decoration: underline;
	}

	:global(.blog-link) {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 8px 12px;
		background: #52c2d0;
		color: white;
		text-decoration: none;
		border-radius: 6px;
		font-size: 13px;
		font-weight: 500;
		transition: all 0.2s ease;
	}

	:global(.blog-link:hover) {
		background: #3a9bb0;
		transform: translateY(-1px);
		box-shadow: 0 2px 8px rgba(82, 194, 208, 0.3);
	}

	:global(.arrow) {
		font-size: 12px;
		transition: transform 0.2s ease;
	}

	:global(.blog-link:hover .arrow) {
		transform: translateX(2px);
	}

	/* カルーセル型ポップアップのスタイル */
	:global(.carousel-popup-container) {
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN',
			'游ゴシック体', YuGothic, sans-serif;
		max-width: 340px;
		min-width: 300px;
		background: #fff;
		border-radius: 10px;
		overflow: hidden;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	:global(.carousel-header) {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 8px 12px;
		background: #f8f9fa;
		border-bottom: 1px solid #e9ecef;
		position: relative;
	}

	:global(.carousel-nav) {
		width: 28px;
		height: 26px;
		border: none;
		border-radius: 5px;
		background: #52c2d0;
		color: white;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
		font-weight: 600;
		transition: all 0.2s ease;
		position: absolute;
	}

	:global(.carousel-prev) {
		left: 30px;
	}

	:global(.carousel-next) {
		right: 30px;
	}

	:global(.carousel-nav:hover:not(:disabled)) {
		background: #3a9bb0;
		transform: scale(1.05);
	}

	:global(.carousel-nav:disabled) {
		background: #dee2e6;
		color: #6c757d;
		cursor: not-allowed;
		transform: none;
	}

	:global(.carousel-counter) {
		font-size: 13px;
		font-weight: 600;
		color: #495057;
		min-width: 50px;
		text-align: center;
	}

	:global(.current-index) {
		color: #52c2d0;
		font-weight: 700;
	}

	:global(.carousel-content) {
		position: relative;
		overflow: hidden;
	}

	:global(.carousel-slide) {
		display: none;
		opacity: 0;
		transform: translateX(20px);
		transition: all 0.3s ease;
	}

	:global(.carousel-slide.active) {
		display: block;
		opacity: 1;
		transform: translateX(0);
	}

	:global(.carousel-slide .poi-card) {
		margin: 0;
		border-radius: 0;
		box-shadow: none;
		border: none;
		padding: 12px;
	}
</style>
