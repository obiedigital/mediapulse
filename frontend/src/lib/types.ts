export interface ArticleListItem {
  id: string
  title: string
  publication: string
  url: string | null
  byline: string | null
  topic_label: string
  published_at: string
  published_at_confidence: string
  status: string
  is_advert: boolean
  pickup_count: number
  category: string | null
  sentiment_overall: string | null
  threat_tag: string | null
  relevance_score: number | null
}

export interface ArticleListResponse {
  items: ArticleListItem[]
  total: number
  limit: number
  offset: number
}

export interface ArticleDetail extends ArticleListItem {
  section: string | null
  page_number: number | null
  fetched_at: string
  raw_text: string
  sentiment_by_brand: Record<string, string>
  entities: Record<string, string[]>
  summary_exec: string | null
  key_quotes: string[]
  why_it_matters: string | null
  threat_rationale: string | null
  model_used: string | null
  classified_at: string | null
}

export interface KPI {
  period_start: string
  period_end: string
  total_articles: number
  classified_count: number
  pending_count: number
  error_count: number
  needs_review_count: number
  sentiment_breakdown: Record<string, number>
  avg_relevance: number | null
  opportunity_count: number
  monitor_count: number
  risk_count: number
}

export interface ShareOfVoicePoint {
  date: string
  brand: string
  mentions: number
}

export interface ShareOfVoice {
  period_start: string
  period_end: string
  points: ShareOfVoicePoint[]
  methodology_note: string
}

export interface SentimentTrendPoint {
  date: string
  brand: string
  positive: number
  neutral: number
  negative: number
}

export interface TopicMixPoint {
  topic_label: string
  category: string | null
  count: number
}

export interface PublicationStat {
  publication: string
  count: number
}

export interface BylineStat {
  byline: string
  publication: string | null
  count: number
}

export interface SourceHealth {
  id: string
  name: string
  type: string
  topic_label: string
  is_active: boolean
  last_fetched_at: string | null
  last_success_at: string | null
  consecutive_error_count: number
  last_error: string | null
}

export interface Brief {
  id: string
  brief_type: string
  status: string
  period_start: string
  period_end: string
  generated_at: string | null
  published_at: string | null
  sent_at: string | null
  html_content?: string | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: string
  tenant_id: string | null
  role: string
  name: string
}

export interface CurrentUser {
  user_id: string
  email: string
  name: string
  role: string
  tenant_id: string | null
}

export interface AskCitation {
  article_id: string
  title: string
}

export interface AskResponse {
  answer: string
  citations: AskCitation[]
}
