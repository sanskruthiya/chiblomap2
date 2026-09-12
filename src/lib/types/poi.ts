export interface POIProperties {
	fid: number;
	name_poi: string;
	title_source: string;
	link_source: string;
	blog_source: string;
	date_text: string;
	date_stamp: number;
	address_poi?: string;
	url_link?: string;
	url_flag?: string;
	flag_poi?: string;
	og_image?: string;
}

export type POIFeature = GeoJSON.Feature<GeoJSON.Point, POIProperties>;

export interface SiteInfo {
	lastDataUpdate: string;
	dataCount: number;
	announcements?: { date: string; message: string }[];
	githubUrl: string;
}
