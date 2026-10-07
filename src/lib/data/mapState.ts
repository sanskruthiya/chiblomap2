export interface SavedMapState {
	center: [number, number];
	zoom: number;
	filterKeyword: string;
	selectedPeriod: number;
	selectedCategories: string[];
	showPOIList: boolean;
	isListExpanded: boolean;
	sortMode: string;
}

const STORAGE_KEY = 'chiblo-map-state';

export function loadMapState(): SavedMapState | null {
	if (typeof sessionStorage === 'undefined') return null;

	try {
		const value = sessionStorage.getItem(STORAGE_KEY);
		if (!value) return null;
		const state = JSON.parse(value) as Partial<SavedMapState>;
		if (
			!Array.isArray(state.center) ||
			state.center.length !== 2 ||
			!state.center.every(Number.isFinite) ||
			!Number.isFinite(state.zoom)
		) {
			return null;
		}
		return {
			center: [state.center[0], state.center[1]],
			zoom: state.zoom as number,
			filterKeyword: typeof state.filterKeyword === 'string' ? state.filterKeyword : '',
			selectedPeriod: Number.isFinite(state.selectedPeriod) ? (state.selectedPeriod as number) : 0,
			selectedCategories: Array.isArray(state.selectedCategories)
				? state.selectedCategories.filter((value): value is string => typeof value === 'string')
				: [],
			showPOIList: state.showPOIList !== false,
			isListExpanded: state.isListExpanded === true,
			sortMode: typeof state.sortMode === 'string' ? state.sortMode : 'name-asc'
		};
	} catch {
		return null;
	}
}

export function saveMapState(state: SavedMapState) {
	if (typeof sessionStorage === 'undefined') return;
	sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}
