<script lang="ts">
	import { onMount } from 'svelte';
	import maplibregl from 'maplibre-gl';
	import { deserialize } from 'flatgeobuf/lib/mjs/geojson.js';
	import 'maplibre-gl/dist/maplibre-gl.css';

	let mapContainer: HTMLDivElement;
	let map: maplibregl.Map;
	let loadingProgress = 0;
	let isDataLoaded = false;
	let popup: maplibregl.Popup | null = null;
	let showPOIList = true;
	let isListExpanded = false;
	let centerPOIs: any[] = [];
	let showDescription = false;
	let showFilter = false;
	let filterKeyword = '';
	let selectedRange = 0;
	let selectedCategory = '';
	let showMenu = false;
	let showLocationSearch = false;
	let searchQuery = '';
	let selectedPeriod = 0; // 0: 全期間, 1: 1ヶ月, 2: 3ヶ月, 3: 6ヶ月, 4: 1年
	let selectedCategories: string[] = []; // 選択されたカテゴリのリスト

	// 初期設定（旧バージョンから引用）
	const INITIAL_COORDS: [number, number] = [139.95, 35.89];
	const INITIAL_ZOOM = 11.5;
	const INITIAL_BEARING = 0;
	const INITIAL_PITCH = 0;

	// POIデータを格納するオブジェクト
	const poiData: GeoJSON.FeatureCollection = {
		type: 'FeatureCollection',
		features: []
	};

	// 期間フィルターの選択肢
	const periodOptions = [
		{ value: 0, label: '全期間', days: null },
		{ value: 1, label: '1ヶ月以内', days: 30 },
		{ value: 2, label: '3ヶ月以内', days: 90 },
		{ value: 3, label: '6ヶ月以内', days: 180 },
		{ value: 4, label: '1年以内', days: 365 }
	];

	// カテゴリフィルターの選択肢（キーワードベース）
	const categoryOptions = [
		{ 
			id: 'cafe', 
			label: 'カフェ', 
			keywords: ['カフェ', 'cafe', '喫茶店', 'コーヒー', 'coffee'] 
		},
		{ 
			id: 'ramen', 
			label: 'ラーメン', 
			keywords: ['ラーメン', 'ramen', 'らーめん', '麺屋'] 
		},
		{ 
			id: 'sushi', 
			label: '寿司', 
			keywords: ['寿司', '鮨'] 
		},
		{ 
			id: 'westernfood', 
			label: '洋食', 
			keywords: ['レストラン', 'イタリアン', 'フレンチ'] 
		},
		{ 
			id: 'park', 
			label: '公園', 
			keywords: ['公園'] 
		}
	];

	// FlatGeoBufデータの読み込み
	async function loadPOIData() {
		try {
			const currentDate = new Date();
			const dateParam = `${currentDate.getFullYear()}${(currentDate.getMonth() + 1).toString().padStart(2, '0')}${currentDate.getDate().toString().padStart(2, '0')}`;
			const url = `/data/poi.fgb?${dateParam}`;
			
			console.log('Loading POI data from:', url);
			
			const response = await fetch(url);
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			if (!response.body) {
				throw new Error('Response body is null');
			}

			let meta: any;
			const iter = deserialize(response.body, undefined, (m: any) => (meta = m));
			
			for await (const feature of iter) {
				poiData.features.push(feature);
				loadingProgress = Math.floor((poiData.features.length / meta.featuresCount) * 100);
				
				// 進捗更新（512件ごとまたは完了時）
				if (poiData.features.length === meta.featuresCount || poiData.features.length % 512 === 0) {
					updateMapData();
				}
			}
			
			isDataLoaded = true;
			console.log(`Loaded ${poiData.features.length} POI features`);
			
		} catch (error) {
			console.error('POIデータの読み込みに失敗しました:', error);
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

	// 複数POI対応のポップアップHTML作成（旧バージョン準拠）
	function createMultiPOIPopupHTML(features: any[]): string {
		// リンクタイプの取得
		const getLinkType = (flag: string) => {
			const types: { [key: string]: string } = {
				'1': '公式サイト',
				'2': '公式Instagram', 
				'3': '公式Twitter'
			};
			return types[flag] || 'リンク';
		};

		let popupContent = '';
		popupContent += '<table class="tablestyle02">';
		popupContent += '<tr><th class="main">ブログ記事 <small style="font-weight: normal; font-size: 11px; color: #fff;">（🔗場所名をクリックで追加リンク表示）</small></th></tr>';
		
		features.forEach(function (feat) {
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

			// ブログ記事リンク
			const blogContent = linkSource ? 
				`<a href="${linkSource}" target="_blank" rel="noopener">${blogSource}${dateText ? `（${dateText}）` : ''}<br>${titleSource}</a>` : 
				`${blogSource}${dateText ? `（${dateText}）` : ''}<br>${titleSource}`;

			// 公式リンクの作成
			const officialLink = urlFlag !== '0' && urlLink ? 
				`<a href="${urlLink}" target="_blank" rel="noopener">🏠 ${getLinkType(urlFlag)}</a> ／ ` : '';
			
			// Google Mapリンク
			const googleMapLink = `<a href="https://www.google.com/maps/search/?api=1&query=${coordinates[1].toFixed(5)},${coordinates[0].toFixed(5)}&zoom=18" target="_blank" rel="noopener">🗺️ Google Map</a>`;
			
			const linkOfficial = officialLink + googleMapLink + '<hr style="margin: 8px 0; border: none; border-top: 1px dotted #ccc;">';

			popupContent += `<tr><td class="main">
				<details>
					<summary>${name}</summary>
					${linkOfficial}
				</details>
				${blogContent}
			</td></tr>`;
		});
		
		popupContent += '</table>';
		return popupContent;
	}

	// マップ中央付近のPOIを取得する関数（旧バージョン準拠）
	function updateCenterPOIs() {
		if (!map || !isDataLoaded) return;

		const center = map.getCenter();
		const point = map.project(center);
		const bbox: [maplibregl.PointLike, maplibregl.PointLike] = [
			[point.x - 30, point.y - 30],  // 左上
			[point.x + 30, point.y + 30]   // 右下
		];
		
		// 旧バージョンと同じピクセルベースの矩形範囲でPOIを取得
		const features = map.queryRenderedFeatures(bbox, { 
			layers: ['poi-points'] 
		});
		
		centerPOIs = features.slice(0, 50); // 最大50件に制限
	}

	// POIリスト表示の切り替え
	function togglePOIList() {
		showPOIList = !showPOIList;
		if (showPOIList) {
			updateCenterPOIs();
		}
	}

	// リストサイズの切り替え
	function toggleListSize() {
		isListExpanded = !isListExpanded;
	}

	// 説明オーバーレイの切り替え
	function toggleDescription() {
		showDescription = !showDescription;
	}

	// フィルターオーバーレイの切り替え
	function toggleFilter() {
		showFilter = !showFilter;
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

	// 期間フィルターの日付計算
	function getPeriodTimestamp(days: number | null): number {
		if (days === null) return 0; // 全期間
		
		const now = new Date();
		const pastDate = new Date(now.getTime() - (days * 24 * 60 * 60 * 1000));
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
			selectedCategories = selectedCategories.filter(id => id !== categoryId);
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
	}

	// 検索ワード + 期間 + カテゴリの複合フィルター
	function applyCombinedFilter() {
		const keyword = filterKeyword.toLowerCase().trim();
		const selectedOption = periodOptions.find(opt => opt.value === selectedPeriod);
		const periodTimestamp = selectedOption ? getPeriodTimestamp(selectedOption.days) : 0;
		
		// 選択されたカテゴリのキーワードを収集
		const categoryKeywords: string[] = [];
		selectedCategories.forEach(categoryId => {
			const category = categoryOptions.find(cat => cat.id === categoryId);
			if (category) {
				categoryKeywords.push(...category.keywords);
			}
		});
		
		// 全POIから条件に一致するものを抽出
		const matchingFeatures = poiData.features.filter(feature => {
			const props = feature.properties;
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
				
				const matchesKeyword = searchTargets.some(target => 
					target.toLowerCase().includes(keyword)
				);
				
				if (!matchesKeyword) return false;
			}
			
			// カテゴリフィルター（name_poiとtitle_sourceのみを対象）
			if (categoryKeywords.length > 0) {
				const categoryTargets = [
					props.name_poi || '',
					props.title_source || ''
				];
				
				const matchesCategory = categoryKeywords.some(categoryKeyword => 
					categoryTargets.some(target => 
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
				.map(feature => feature.properties?.fid)
				.filter(fid => fid !== undefined);
			
			// MapLibre GL JSのフィルター式を作成
			const filterExpression: any = ['match', ['get', 'fid'], matchingFids, true, false];
			
			// 各レイヤーにフィルターを適用
			map.setFilter('poi-points', filterExpression);
			map.setFilter('poi-heat', filterExpression);
			map.setFilter('poi-text', filterExpression);
		} else {
			// 検索結果が0件の場合、全てのPOIを非表示
			const noResultFilter: any = ['has', 'poi_nonexistent'];
			map.setFilter('poi-points', noResultFilter);
			map.setFilter('poi-heat', noResultFilter);
			map.setFilter('poi-text', noResultFilter);
		}
	}

	// 検索ワードフィルターの適用
	function applyKeywordFilter() {
		const keyword = filterKeyword.toLowerCase().trim();
		
		// 全POIから検索ワードに一致するものを抽出
		const matchingFeatures = poiData.features.filter(feature => {
			const props = feature.properties;
			if (!props) return false;
			
			const searchTargets = [
				props.name_poi || '',
				props.flag_poi || '',
				props.blog_source || '',
				props.title_source || ''
			];
			
			return searchTargets.some(target => 
				target.toLowerCase().includes(keyword)
			);
		});

		if (matchingFeatures.length > 0) {
			// 一致するPOIのfidリストを作成
			const matchingFids = matchingFeatures
				.map(feature => feature.properties?.fid)
				.filter(fid => fid !== undefined);
			
			// MapLibre GL JSのフィルター式を作成（型安全）
			const filterExpression: any = ['match', ['get', 'fid'], matchingFids, true, false];
			
			// 各レイヤーにフィルターを適用
			map.setFilter('poi-points', filterExpression);
			map.setFilter('poi-heat', filterExpression);
			map.setFilter('poi-text', filterExpression);
		} else {
			// 検索結果が0件の場合、全てのPOIを非表示
			const noResultFilter: any = ['has', 'poi_nonexistent'];
			map.setFilter('poi-points', noResultFilter);
			map.setFilter('poi-heat', noResultFilter);
			map.setFilter('poi-text', noResultFilter);
		}
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
		selectedRange = 0;
		selectedCategory = '';
		selectedPeriod = 0;
		selectedCategories = [];
		applyFilter();
	}

	// ハンバーガーメニューの切り替え
	function toggleMenu() {
		showMenu = !showMenu;
	}

	// 場所検索モーダルの切り替え
	function toggleLocationSearch() {
		showLocationSearch = !showLocationSearch;
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
		// MapLibre GL JSマップの初期化
		map = new maplibregl.Map({
			container: mapContainer,
			style: '/data/basemap_style.json',
			center: INITIAL_COORDS,
			zoom: INITIAL_ZOOM,
			bearing: INITIAL_BEARING,
			pitch: INITIAL_PITCH,
			maxZoom: 18,
			minZoom: 8
		});

		// マップの読み込み完了時の処理
		map.on('load', () => {
			console.log('Map loaded successfully');
			
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
					'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 
						0, 'rgba(200,255,255,0)', 
						0.4, '#e0ffff', 
						1, '#00bfff'
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

			// データ読み込み開始
			loadPOIData();
		});

		// データ読み込み完了時にPOIリストを初期表示
		map.on('sourcedata', (e) => {
			if (e.sourceId === 'poi-data' && e.isSourceLoaded && isDataLoaded) {
				updateCenterPOIs();
			}
		});

		// POIクリックイベントを追加（複数POI対応）
		map.on('click', 'poi-points', (e) => {
			// 既存のポップアップを削除
			if (popup) {
				popup.remove();
			}
			
			// クリック箇所の全てのPOI情報を取得
			const features = map.queryRenderedFeatures(e.point, { layers: ['poi-points'] });
			
			if (features.length > 0) {
				// 新しいポップアップを作成
				popup = new maplibregl.Popup({
					closeButton: true,
					closeOnClick: false,
					anchor: 'bottom',
					maxWidth: '360px',
					className: 'scrollable-popup'
				})
				.setLngLat(e.lngLat)
				.setHTML(createMultiPOIPopupHTML(features))
				.addTo(map);
			}
		});

		// マウスカーソルの変更
		map.on('mouseenter', 'poi-points', () => {
			map.getCanvas().style.cursor = 'pointer';
		});

		map.on('mouseleave', 'poi-points', () => {
			map.getCanvas().style.cursor = '';
		});

		// ナビゲーションコントロールを追加
		map.addControl(new maplibregl.NavigationControl(), 'top-right');

		// マップ移動時にPOIリストを更新
		map.on('moveend', () => {
			if (showPOIList) {
				updateCenterPOIs();
			}
		});

		// 初期POIリスト表示
		if (isDataLoaded) {
			updateCenterPOIs();
		}

		// クリーンアップ関数
		return () => {
			map?.remove();
		};
	});
</script>

<div class="relative h-full w-full">
	<!-- マップコンテナ -->
	<div bind:this={mapContainer} class="h-full w-full"></div>
	
	<!-- ローディング表示 -->
	{#if !isDataLoaded}
		<div class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-10">
			<div class="text-center">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
				<p class="text-lg font-medium text-gray-700">POIデータを読み込み中...</p>
				<p class="text-sm text-gray-500">{loadingProgress}% 完了</p>
			</div>
		</div>
	{/if}

	<!-- ハンバーガーメニューボタン -->
	<div class="hamburger-container">
		<button 
			type="button" 
			class="hamburger-button" 
			on:click={toggleMenu}
			aria-expanded={showMenu}
			aria-label="メニューを開く"
		>
			<div class="hamburger-icon" class:active={showMenu}>
				<span></span>
				<span></span>
				<span></span>
			</div>
		</button>
		
		<!-- ドロップダウンメニュー -->
		{#if showMenu}
			<div class="dropdown-menu">
				<button 
					type="button" 
					class="menu-item" 
					on:click={() => handleMenuAction('description')}
				>
					<svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10"></circle>
						<path d="M9,9h6v6H9z"></path>
						<path d="M9 1v6M15 1v6M9 17v6M15 17v6M1 9h6M1 15h6M17 9h6M17 15h6"></path>
					</svg>
					このマップについて
				</button>
				<button 
					type="button" 
					class="menu-item" 
					on:click={() => handleMenuAction('location')}
				>
					<svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
						<circle cx="12" cy="10" r="3"></circle>
					</svg>
					場所を調べる
				</button>
				<button 
					type="button" 
					class="menu-item" 
					on:click={() => handleMenuAction('filter')}
				>
					<svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46 22,3"></polygon>
					</svg>
					フィルター絞り込み
				</button>
			</div>
		{/if}
	</div>

	<!-- 画面中央の十字アイコン（検索範囲表示） -->
	<div class="crosshair">
		<svg focusable="false" width="100px" height="100px" viewBox="-0.5 0 25 25" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M21.5001 12.5H16.5601" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M7.44 12.5H2.5" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M12 22V17.06" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M12 7.94V3" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M5.26001 10.5C5.93001 8.22 7.73001 6.41999 10.01 5.75999" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M14.01 19.24C16.29 18.58 18.09 16.78 18.76 14.5" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M5.26001 14.5C5.93001 16.78 7.73001 18.58 10.01 19.24" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
			<path d="M14.01 5.75999C16.29 6.41999 18.09 8.22 18.76 10.5" stroke="rgba(100,100,100,0.5)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
	</div>

	<!-- POIリスト表示 -->
	{#if showPOIList}
		<div class="poi-list-overlay" class:large-screen={isListExpanded}>
			<div class="poi-list-header">
				<h3 class="poi-list-title">記事一覧</h3>
				<div class="poi-list-controls">
					<button 
						class="expand-button"
						on:click={toggleListSize}
						aria-label={isListExpanded ? 'リストを縮小' : 'リストを拡大'}
					>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							{#if isListExpanded}
								<path d="M18 15l-6-6-6 6"></path>
							{:else}
								<path d="M6 9l6 6 6-6"></path>
							{/if}
						</svg>
					</button>
					<button 
						class="collapse-button"
						on:click={() => showPOIList = false}
						aria-label="記事一覧を非表示"
					>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="18" y1="6" x2="6" y2="18"></line>
							<line x1="6" y1="6" x2="18" y2="18"></line>
						</svg>
					</button>
				</div>
			</div>
			
			<p class="poi-count">マップ中央付近の記事数：{centerPOIs.length}</p>
			
			{#if centerPOIs.length > 0}
				{#each centerPOIs as poi}
					<a 
						href={poi.properties.link_source} 
						target="_blank" 
						rel="noopener"
						class="poi-item"
					>
						<strong>{poi.properties.name_poi}</strong> 
						({poi.properties.blog_source} {poi.properties.date_text}) 
						{poi.properties.title_source}
					</a>
					<hr class="poi-divider">
				{/each}
			{:else}
				<p class="poi-count">マップ中央付近に記事がありません。</p>
			{/if}
		</div>
	{:else}
		<!-- POIリストが非表示の時の再表示ボタン -->
		<button 
			class="show-list-button"
			on:click={() => showPOIList = true}
			aria-label="記事一覧を表示"
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
				<line x1="16" y1="2" x2="16" y2="6"></line>
				<line x1="8" y1="2" x2="8" y2="6"></line>
				<line x1="3" y1="10" x2="21" y2="10"></line>
			</svg>
			記事一覧
		</button>
	{/if}

	<!-- 説明オーバーレイ -->
	{#if showDescription}
		<div class="description-overlay">
			<div class="description-content">
				<div class="description-header">
					<h2>ちーぶろマップ</h2>
					<button 
						type="button" 
						class="close-button" 
						on:click={toggleDescription}
						aria-label="説明を閉じる"
					>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="18" y1="6" x2="6" y2="18"></line>
							<line x1="6" y1="6" x2="18" y2="18"></line>
						</svg>
					</button>
				</div>
				<p class="tipstyle01">東葛地域とつくばエクスプレス沿線を中心に、柏市・流山市・松戸市・野田市・我孫子市・守谷市とその周辺の地域ブロガーの方々が発信しているブログ記事を、地図上の場所とリンクさせて表示するマップです。</p>
				<p class="tipstyle01">地図上の水色の円をクリック/タップすると、その場所のお店やおすすめスポットのブログ記事が一覧で表示されます。</p>
				<p class="tipstyle01">ご意見等は<a href="https://form.run/@party--1681740493" target="_blank">問い合わせフォーム（外部サービス）</a>からお知らせください。</p>
			</div>
		</div>
	{/if}

	<!-- 場所検索モーダル -->
	{#if showLocationSearch}
		<div class="location-search-overlay">
			<div class="location-search-content">
				<div class="location-search-header">
					<h2>場所を調べる</h2>
					<button 
						type="button" 
						class="close-button" 
						on:click={toggleLocationSearch}
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
						on:click={getCurrentLocation}
					>
						<svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"></path>
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
							on:keydown={(e) => e.key === 'Enter' && searchLocation()}
							class="search-input"
						>
						<button 
							type="button" 
							class="location-action-button search-btn"
							on:click={searchLocation}
						>
							<svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<circle cx="11" cy="11" r="8"></circle>
								<path d="m21 21-4.35-4.35"></path>
							</svg>
							検索
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- フィルターオーバーレイ -->
	{#if showFilter}
		<div class="filter-overlay">
			<div class="filter-overlay-inner">
				<div class="filter-header">
					<h2>フィルター絞り込み</h2>
					<button 
						type="button" 
						class="close-button" 
						on:click={toggleFilter}
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
							on:input={applyFilter}
							class="filter-input"
						>
						<button type="button" class="clearbutton" on:click={clearFilter} aria-label="検索ワードをクリア">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="18" y1="6" x2="6" y2="18"></line>
								<line x1="6" y1="6" x2="18" y2="18"></line>
							</svg>
						</button>
					</div>
				</div>

				<!-- 期間フィルター -->
				<div class="filter-section">
					<h3>期間</h3>
					<p class="filter-description">記事の投稿時期で絞り込み</p>
					<div class="period-chips">
						{#each periodOptions as option}
							<button 
								type="button"
								class="chip" 
								class:active={selectedPeriod === option.value}
								on:click={() => selectPeriod(option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- カテゴリフィルター -->
				<div class="filter-section">
					<h3>カテゴリ</h3>
					<p class="filter-description">店名・記事タイトルからカテゴリで絞り込み</p>
					<div class="category-chips">
						{#each categoryOptions as category}
							<button 
								type="button"
								class="chip" 
								class:active={selectedCategories.includes(category.id)}
								on:click={() => toggleCategory(category.id)}
							>
								{category.label}
							</button>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	/* MapLibre GL JSのスタイルを確実に適用 */
	:global(.maplibregl-map) {
		font-family: inherit;
	}

	/* 旧バージョン準拠のポップアップスタイル */
	:global(.scrollable-popup .maplibregl-popup-content) {
		background: #fff;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
		padding: 8px 10px;
		overflow-y: scroll !important;
		max-height: 210px;
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
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
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
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
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

	/* POIリスト表示のスタイル（旧バージョン準拠） */
	.poi-list-overlay {
		position: absolute;
		overflow-y: scroll;
		max-height: 15%;
		width: 80%;
		max-width: 600px;
		bottom: 40px;
		left: 5px;
		padding: 8px 20px;
		background: rgba(250, 250, 250, 0.9);
		box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
		border-radius: 3px;
		border: 1px solid #999;
		line-height: 18px;
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
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

	/* POIリストヘッダーのスタイル */
	.poi-list-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 15px;
		background: rgba(255, 255, 255, 0.95);
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
		margin: -10px -10px 10px -10px;
	}

	.poi-list-title {
		color: #333;
		font-size: 14px;
		font-weight: 600;
		margin: 0;
	}

	.poi-list-controls {
		display: flex;
		gap: 8px;
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

	/* POIリスト再表示ボタンのスタイル */
	.show-list-button {
		position: fixed;
		bottom: 20px;
		left: 20px;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #52c2d0;
		border-radius: 8px;
		padding: 10px 15px;
		font-size: 13px;
		font-family: inherit;
		color: #52c2d0;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 8px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		transition: all 0.2s ease;
		z-index: 20;
	}

	.show-list-button:hover {
		background: #52c2d0;
		color: white;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(82, 194, 208, 0.3);
	}

	.show-list-button svg {
		width: 16px;
		height: 16px;
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

	/* ハンバーガーメニューのスタイル */
	.hamburger-container {
		position: absolute;
		top: 16px;
		left: 16px;
		z-index: 30;
	}

	.hamburger-button {
		background-color: rgba(255, 255, 255, 0.95);
		border: none;
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
		background-color: #333;
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

	/* ドロップダウンメニューのスタイル */
	.dropdown-menu {
		position: absolute;
		top: 60px;
		left: 0;
		background-color: rgba(255, 255, 255, 0.95);
		border-radius: 8px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
		backdrop-filter: blur(10px);
		min-width: 200px;
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
		padding: 12px 16px;
		text-align: left;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 12px;
		font-size: 14px;
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
		color: #333;
		transition: background-color 0.2s ease;
	}

	.menu-item:hover {
		background-color: rgba(52, 194, 208, 0.1);
	}

	.menu-item:active {
		background-color: rgba(52, 194, 208, 0.2);
	}

	.menu-icon {
		width: 18px;
		height: 18px;
		color: #52c2d0;
		flex-shrink: 0;
	}

	/* 説明オーバーレイのスタイル */
	.description-overlay {
		position: absolute;
		top: 10px;
		right: 10px;
		width: 300px;
		max-width: 90vw;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #999;
		border-radius: 8px;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		z-index: 30;
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
		backdrop-filter: blur(10px);
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

	.description-content h2 {
		color: #111;
		font-size: 18px;
		font-weight: normal;
		margin: 0;
		text-align: left;
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
		color: #333;
		font-size: 12px;
		font-weight: normal;
		line-height: 1.4;
		margin: 8px 0;
	}

	.tipstyle01 a {
		color: #3498db;
		text-decoration: underline;
	}

	/* フィルターオーバーレイのスタイル */
	.filter-overlay {
		position: absolute;
		top: 10px;
		right: 10px;
		width: 250px;
		max-width: 90vw;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #999;
		border-radius: 3px;
		padding: 15px;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		z-index: 30;
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
	}

	/* フィルターモーダルのスタイル */
	.filter-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 15px 15px 10px 15px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
		margin-bottom: 15px;
	}

	.filter-header h2 {
		color: #111;
		font-size: 18px;
		font-weight: normal;
		margin: 0;
		text-align: left;
	}

	.filter-section {
		margin-bottom: 20px;
		padding-bottom: 15px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}

	.filter-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
	}

	.filter-section h3 {
		color: #333;
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 5px 0;
	}

	.filter-description {
		color: #666;
		font-size: 12px;
		margin: 0 0 10px 0;
		line-height: 1.4;
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

	.clearbutton {
		position: absolute;
		right: 8px;
		top: 50%;
		transform: translateY(-50%);
		background: none;
		border: none;
		color: #999;
		cursor: pointer;
		padding: 4px;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
		transition: all 0.2s ease;
	}

	.clearbutton:hover {
		color: #333;
		background-color: rgba(0, 0, 0, 0.1);
	}

	.clearbutton svg {
		width: 16px;
		height: 16px;
	}

	/* カテゴリチップのスタイル */
	.category-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 8px;
	}

	/* 期間チップのスタイル */
	.period-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 8px;
	}

	.chip {
		background-color: rgba(255, 255, 255, 0.9);
		border: 1px solid #ddd;
		border-radius: 20px;
		padding: 6px 12px;
		font-size: 12px;
		font-family: inherit;
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

	/* 場所検索モーダルのスタイル */
	.location-search-overlay {
		position: absolute;
		top: 10px;
		right: 10px;
		width: 350px;
		max-width: 90vw;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid #999;
		border-radius: 8px;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		z-index: 30;
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
		backdrop-filter: blur(10px);
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
</style>
