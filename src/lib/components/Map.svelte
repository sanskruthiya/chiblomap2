<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import maplibregl from 'maplibre-gl';
	import { deserialize } from 'flatgeobuf/lib/mjs/geojson.js';
	import { base } from '$app/paths';
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
	let centerPOIs: any[] = [];
	let showDescription = false;
	let showFilter = false;
	let filterKeyword = '';
	let selectedRange = 0;
	let selectedCategory = '';
	let showMenu = false;
	let showLocationSearch = false;
	let searchQuery = '';
	let selectedStation = ''; // 選択された駅
	let selectedPeriod = 0; // 0: 全期間, 1: 1ヶ月, 2: 3ヶ月, 3: 6ヶ月, 4: 1年
	let selectedCategories: string[] = []; // 選択されたカテゴリのリスト
	let sortMode = 'name-asc'; // ソートモード: 'name-asc'(デフォルト), 'date-desc'
	let totalPOICount = 0; // 実際のPOI総数（リアクティブ変数）
	let currentVisiblePOIs = 0; // 現在表示されているPOI数（フィルター適用後）
	let siteInfo: any = null; // サイト情報（外部JSONから読み込み）
	let currentPopupFeatures: any[] = []; // 現在のポップアップに表示するPOI一覧
	let currentPopupIndex = 0; // カルーセルの現在のインデックス

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

	// 駅の選択肢
	const stationOptions = [
		{ 
			id: '', 
			name: '駅を選択してください', 
			lat: null, 
			lng: null 
		},
		{ 
			id: 'minami-nagareyama', 
			name: '南流山', 
			lat: 35.8381, 
			lng: 139.9035 
		},
		{ 
			id: 'nagareyama-central-park', 
			name: '流山セントラルパーク', 
			lat: 35.8546, 
			lng: 139.9152 
		},
		{ 
			id: 'nagareyama-otakanomori', 
			name: '流山おおたかの森', 
			lat: 35.8719, 
			lng: 139.9254 
		},
		{ 
			id: 'kashiwanoha-campus', 
			name: '柏の葉キャンパス', 
			lat: 35.8933, 
			lng: 139.9525 
		},
		{ 
			id: 'kashiwa-tanaka', 
			name: '柏たなか', 
			lat: 35.9109, 
			lng: 139.9575 
		},
		{ 
			id: 'moriya', 
			name: '守谷', 
			lat: 35.9504, 
			lng: 139.9921 
		},
		{ 
			id: 'mirai-daira', 
			name: 'みらい平', 
			lat: 35.9944, 
			lng: 140.0383 
		},
		{ 
			id: 'midorino', 
			name: 'みどりの', 
			lat: 36.0299, 
			lng: 140.0562 
		},
		{ 
			id: 'kenkyugakuen', 
			name: '研究学園', 
			lat: 36.0822, 
			lng: 140.0823 
		},
		{ 
			id: 'banpaku-kinen-koen', 
			name: '万博記念公園', 
			lat: 36.0584, 
			lng: 140.0594 
		},
		{ 
			id: 'tsukuba', 
			name: 'つくば', 
			lat: 36.0824, 
			lng: 140.1105 
		},
		{ 
			id: 'matsudo', 
			name: '松戸', 
			lat: 35.7846, 
			lng: 139.9008 
		},
		{ 
			id: 'kashiwa', 
			name: '柏', 
			lat: 35.8621, 
			lng: 139.9708 
		},
		{ 
			id: 'shin-matsudo', 
			name: '新松戸', 
			lat: 35.8254, 
			lng: 139.9212 
		},
		{ 
			id: 'minami-kashiwa', 
			name: '南柏', 
			lat: 35.8446, 
			lng: 139.9542 
		},
		{ 
			id: 'abiko', 
			name: '我孫子', 
			lat: 35.8728, 
			lng: 140.0105 
		},
		{ 
			id: 'toride', 
			name: '取手', 
			lat: 35.8963, 
			lng: 140.0632 
		},
		{ 
			id: 'edogawadai', 
			name: '江戸川台', 
			lat: 35.8972, 
			lng: 139.9105 
		},
		{ 
			id: 'hatsuishi', 
			name: '初石', 
			lat: 35.8838, 
			lng: 139.9179 
		},
		{ 
			id: 'unga', 
			name: '運河', 
			lat: 35.9144, 
			lng: 139.906 
		},
		{ 
			id: 'shimizu-koen', 
			name: '清水公園', 
			lat: 35.9588, 
			lng: 139.8603 
		},
		{ 
			id: 'nagareyama', 
			name: '流山', 
			lat: 35.8558, 
			lng: 139.9018 
		},
		{ 
			id: 'toyoshiki', 
			name: '豊四季', 
			lat: 35.8665, 
			lng: 139.9393 
		},
		{ 
			id: 'sakasai', 
			name: '逆井', 
			lat: 35.8233, 
			lng: 139.9837 
		},
		{ 
			id: 'shin-yahashira', 
			name: '新八柱', 
			lat: 35.7913, 
			lng: 139.9386 
		}
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
			id: 'izakaya', 
			label: '居酒屋', 
			keywords: ['居酒屋', '呑み'] 
		},
		{ 
			id: 'park', 
			label: '公園', 
			keywords: ['公園'] 
		}
	];

	// サイト情報の読み込み
	async function loadSiteInfo() {
		try {
			const response = await fetch(`${base}/data/site-info.json`);
			if (!response.ok) throw new Error('サイト情報の取得に失敗しました');
			siteInfo = await response.json();
			return siteInfo;
		} catch (error) {
			console.error('サイト情報の読み込みに失敗しました:', error);
			// フォールバック用のデフォルト値
			siteInfo = {
				lastDataUpdate: "2025年12月15日",
				dataCount: 2568,
				announcements: [],
				githubUrl: "https://github.com/sanskruthiya/chiblo-map"
			};
			return siteInfo;
		}
	}

	// FlatGeoBufデータの読み込み
	async function loadPOIData(lastDataUpdate?: string) {
		try {
			// lastDataUpdateをキャッシュパラメータとして使用
			let cacheParam = 'default';
			if (lastDataUpdate) {
				// 日本語の日付を英数字のみのパラメータに変換
				cacheParam = lastDataUpdate.replace(/[年月日]/g, '').replace(/\s/g, '');
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

			let meta: any;
			let totalFeatures = 0;
			const iter = deserialize(response.body, undefined, (m: any) => {
				meta = m;
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
				poiData.features.push(feature);
				
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
				if ((totalFeatures > 0 && poiData.features.length === totalFeatures) || poiData.features.length % 256 === 0) {
					updateMapData();
				}
			}
			
			isDataLoaded = true;
			currentVisiblePOIs = poiData.features.length; // 初期状態では全POIが表示
			console.log(`Loaded ${poiData.features.length} POI features`);
			
		} catch (error) {
			console.error('POIデータの読み込みに失敗しました:', error);
			
			// エラー時もローディング完了として扱い、空のデータでマップを表示
			isDataLoaded = true;
			
			// エラー情報を親コンポーネントに通知
			const errorMessage = error instanceof Error ? error.message : 'データの読み込みに失敗しました';
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
	function createMultiPOIPopupHTML(features: any[]): string {
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
		const createSingleCard = (feat: any) => {
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
	function sortPOIs(pois: any[]): any[] {
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
		
		totalPOICount = features.length; // 実際の総数を保存
		const limitedFeatures = features.slice(0, 99); // 最大99件に制限
		centerPOIs = sortPOIs(limitedFeatures); // ソートを適用
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
		
		// 現在表示されているPOI数を更新
		currentVisiblePOIs = matchingFeatures.length;
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
		
		// 全てのフィルターをクリア
		if (map && isDataLoaded) {
			map.setFilter('poi-points', null);
			map.setFilter('poi-heat', null);
			map.setFilter('poi-text', null);
			
			// 現在表示されているPOI数を全件に戻す
			currentVisiblePOIs = poiData.features.length;
		}
	}

	// ハンバーガーメニューの切り替え
	function toggleMenu() {
		showMenu = !showMenu;
	}

	// 場所検索モーダルの切り替え
	function toggleLocationSearch() {
		showLocationSearch = !showLocationSearch;
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

		const station = stationOptions.find(s => s.id === selectedStation);
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
			(window as any).navigatePopup = navigatePopup;

			// URLクエリパラメータから初期表示駅を取得
			const urlParams = new URLSearchParams(window.location.search);
			const stationParam = urlParams.get('station');
			let initCenter: [number, number] = INITIAL_COORDS;
			let initZoom = INITIAL_ZOOM;

			if (stationParam) {
				const matchedStation = stationOptions.find(s => s.id === stationParam);
				if (matchedStation && matchedStation.lat && matchedStation.lng) {
					initCenter = [matchedStation.lng, matchedStation.lat];
					initZoom = 14;
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

			// データ読み込み開始（サイト情報のlastDataUpdateを使用）
			loadPOIData(siteData?.lastDataUpdate);

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
					.setHTML(createMultiPOIPopupHTML(features))
					.addTo(map);
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
			map.addControl(new maplibregl.NavigationControl({
				showCompass: false
			}), 'top-right');

			// ジオロケーションコントロールを追加
			map.addControl(new maplibregl.GeolocateControl({
				positionOptions: {
					enableHighAccuracy: true
				},
				trackUserLocation: true
			}), 'top-right');

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
		});
	});

		// クリーンアップ関数
		return () => {
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
				<div class="poi-list-title-section">
					<h3 class="poi-list-title">マップ中央付近の記事一覧</h3>
					<span class="poi-count-badge">{totalPOICount > 99 ? '99+' : totalPOICount}</span>
				</div>
				
				<!-- ソートボタン -->
				<div class="sort-controls" style="display: none;">
					<button 
						class="sort-button"
						class:active={sortMode === 'name-asc'}
						on:click={() => changeSortMode('name-asc')}
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
						on:click={() => changeSortMode('date-desc')}
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
						on:click={toggleListSize}
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
			
			<div class="poi-list-content">
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
		</button>
	{/if}

	<!-- 説明オーバーレイ -->
	{#if showDescription}
		<div class="modal-backdrop" role="button" tabindex="0" on:click={toggleDescription} on:keydown={(e) => e.key === 'Escape' && toggleDescription()}></div>
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
				
				{#if siteInfo}
					<hr class="section-divider">
					
					<p class="info-item"><strong>記事データ更新日：</strong>{siteInfo.lastDataUpdate}</p>
					
					{#if siteInfo.announcements && siteInfo.announcements.length > 0}
						<div class="announcements">
							<p class="info-title"><strong>お知らせ</strong></p>
							{#each siteInfo.announcements as announcement}
								<p class="announcement-item">• {announcement.message}</p>
							{/each}
						</div>
					{/if}
					
					<hr class="section-divider">
					
					<p class="github-link">
						<a href={siteInfo.githubUrl} target="_blank" rel="noopener noreferrer">
							View code on GitHub
						</a>
					</p>
				{/if}
			</div>
		</div>
	{/if}

	<!-- 場所検索モーダル -->
	{#if showLocationSearch}
		<div class="modal-backdrop" role="button" tabindex="0" on:click={toggleLocationSearch} on:keydown={(e) => e.key === 'Escape' && toggleLocationSearch()}></div>
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

				<!-- 駅名を選択 -->
				<div class="location-section">
					<h3>駅名を選択</h3>
					<p class="section-description">主要駅を選択してマップに移動します</p>
					<div class="station-select-container">
						<select 
							bind:value={selectedStation}
							on:change={selectStation}
							class="station-select"
						>
							{#each stationOptions as station}
								<option value={station.id}>{station.name}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- フィルターオーバーレイ -->
	{#if showFilter}
		<div class="modal-backdrop" role="button" tabindex="0" on:click={toggleFilter} on:keydown={(e) => e.key === 'Escape' && toggleFilter()}></div>
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
					<p class="filter-description">店名・記事タイトルから絞り込み（複数選択可能）</p>
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

				<!-- リセットボタン -->
				<div class="filter-reset-section">
					<button 
						type="button" 
						class="filter-reset-button"
						on:click={clearFilter}
					>
						<svg class="reset-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
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

	/* POIリストヘッダーのスタイル */
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

	/* ソートコントロールのスタイル */
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

	/* POIリストコンテンツのスタイル */
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

	/* POIリスト再表示ボタンのスタイル */
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

	/* ドロップダウンメニューのスタイル */
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

	/* モーダル背景オーバーレイ */
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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

	/* 説明オーバーレイのスタイル */
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
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
		backdrop-filter: blur(10px);
		overflow-y: auto;
		animation: modalFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
	}

	.announcements {
		margin: 16px 0;
	}

	.info-title {
		color: #2c3e50;
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 8px 0;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
	}

	.announcement-item {
		color: #555;
		font-size: 13px;
		line-height: 1.5;
		margin: 4px 0;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
	}

	.github-link a:hover {
		text-decoration: underline;
	}

	/* カード型ポップアップのスタイル */
	:global(.popup-container) {
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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

	/* フィルターオーバーレイのスタイル */
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
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
		backdrop-filter: blur(10px);
		overflow-y: auto;
		animation: modalFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
	}

	/* フィルターモーダルのスタイル */
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
	}

	.filter-description {
		color: #555;
		font-size: 14px;
		margin: 0 0 10px 0;
		line-height: 1.4;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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


	/* カテゴリチップのスタイル */
	.category-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 6px;
		line-height: 1.2;
	}

	/* 期間チップのスタイル */
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

	/* 場所検索モーダルのスタイル */
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
		font-family: Helvetica, "游ゴシック体", YuGothic, "YuGothic M", sans-serif;
		backdrop-filter: blur(10px);
		overflow-y: auto;
		animation: modalFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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

	/* 駅選択ドロップダウンのスタイル */
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

	/* フィルターリセットボタンのスタイル */
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
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "游ゴシック体", YuGothic, sans-serif;
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
</style>
