export type SlideType = "poll" | "word_cloud" | "rating_scale" | "open_text";

export interface PollConfig {
  question: string;
  options: string[];
  multi?: boolean; // allow selecting more than one option
}

export interface WordCloudConfig {
  prompt: string;
  maxWords?: number; // per participant, default 3
}

export interface RatingScaleConfig {
  question: string;
  min: number; // e.g. 1
  max: number; // e.g. 5 or 10
  minLabel?: string;
  maxLabel?: string;
}

export interface OpenTextConfig {
  prompt: string;
}

export type SlideConfig = PollConfig | WordCloudConfig | RatingScaleConfig | OpenTextConfig;

export interface PollValue {
  choices: number[]; // indices into config.options
}

export interface WordCloudValue {
  words: string[];
}

export interface RatingValue {
  rating: number;
}

export interface OpenTextValue {
  text: string;
}

export type ResponseValue = PollValue | WordCloudValue | RatingValue | OpenTextValue;

export interface DemographicTags {
  age_band?: string;
  region?: string;
  gender?: string;
  lsm_segment?: string;
}

export const AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55+"];
export const BW_REGIONS = [
  "Gaborone",
  "Francistown",
  "Maun",
  "Kasane",
  "Palapye",
  "Serowe",
  "Molepolole",
  "Other",
];
export const LSM_SEGMENTS = ["LSM 1-3", "LSM 4-6", "LSM 7-8", "LSM 9-10"];
