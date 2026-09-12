export interface PeriodOption {
	value: number;
	label: string;
	days: number | null;
}

export const periodOptions: PeriodOption[] = [
	{ value: 0, label: '全期間', days: null },
	{ value: 1, label: '1ヶ月以内', days: 30 },
	{ value: 2, label: '3ヶ月以内', days: 90 },
	{ value: 3, label: '6ヶ月以内', days: 180 },
	{ value: 4, label: '1年以内', days: 365 }
];
