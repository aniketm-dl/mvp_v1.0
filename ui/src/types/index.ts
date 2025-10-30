export interface AirlineTwin {
  id: string
  label: string
  demographics: {
    gender: string
    age: number
    age_band: string
  }
  psychographics: string[]
  travel_profile: {
    customer_type: string
    type_of_travel: string
    flight_class: string
    flight_distance: number
    distance_band: string
    delay_band: string
  }
}

export interface TwinDecision {
  twin_id: string
  twin_label: string
  task: {
    task_type: string
    offer: {
      name: string
      offer_kind: string
      discount_pct: number
      absolute_price_delta: number
      constraints: string[]
    }
    context: {
      flight_length: string
      trip_purpose: string
      time_pressure: string
      recent_delays: string
    }
  }
  response: {
    decision: 'yes' | 'no'
    probability: number
    rationale: string
  }
  metadata: {
    timestamp: string
    seed?: number
    llm_metadata?: any
  }
}

export interface ExperimentConfig {
  offerType: string
  discountPct: number
  flightLength: string
  tripPurpose: string
  timePressure: string
  recentDelays: string
  seed?: number
}

export type ViewMode = 'experiment' | 'chat'

// Chat types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: any
}

export interface Conversation {
  id: string
  twin_id: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
  preview?: string
  message_count?: number
}

export interface ChatExperimentResult {
  conversation_id: string
  decision: TwinDecision
}
