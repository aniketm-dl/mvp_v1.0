import axios from 'axios'
import type { AirlineTwin, TwinDecision, ExperimentConfig, Conversation, ChatExperimentResult } from '../types'
import { getTwinName } from '../utils/twinNames'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const twinsAPI = {
  // Get all airline twins
  getAll: async (): Promise<{ twins: AirlineTwin[]; count: number }> => {
    const response = await api.get('/airline/twins')
    return response.data
  },

  // Make a single decision
  decide: async (
    twinId: string,
    config: ExperimentConfig
  ): Promise<TwinDecision> => {
    const response = await api.post('/airline/decide', {
      twin_id: twinId,
      offer_type: config.offerType,
      discount_pct: config.discountPct,
      flight_length: config.flightLength,
      trip_purpose: config.tripPurpose,
      time_pressure: config.timePressure,
      recent_delays: config.recentDelays,
      seed: config.seed,
    })
    return response.data
  },

  // Batch decision for multiple twins
  batchDecide: async (
    twinIds: string[],
    config: ExperimentConfig
  ): Promise<{
    results: TwinDecision[]
    errors: { twin_id: string; error: string }[]
    total: number
    successful: number
    failed: number
  }> => {
    const response = await api.post('/airline/batch_decide', {
      twin_ids: twinIds,
      offer_type: config.offerType,
      discount_pct: config.discountPct,
      flight_length: config.flightLength,
      trip_purpose: config.tripPurpose,
      time_pressure: config.timePressure,
      recent_delays: config.recentDelays,
      seed: config.seed,
    })
    return response.data
  },

  // Export decisions
  exportDecisions: async (format: 'json' | 'csv' = 'json'): Promise<any> => {
    const response = await api.get(`/airline/decisions/export?format=${format}`)
    return response.data
  },
}

export const chatAPI = {
  // Send a message to a twin
  sendMessage: async (
    twinId: string,
    message: string,
    conversationId?: string
  ): Promise<{
    conversation_id: string
    user_message: any
    twin_response: any
  }> => {
    const response = await api.post('/airline/chat/send', {
      twin_id: twinId,
      message: message,
      conversation_id: conversationId,
      context: null
    })

    // The response already has the correct format from our new endpoint
    return response.data
  },

  // Run experiment within chat
  runExperiment: async (
    twinId: string,
    conversationId: string,
    config: ExperimentConfig
  ): Promise<ChatExperimentResult> => {
    // For now, simulate an experiment result since the endpoint doesn't exist
    const decision: TwinDecision = {
      twin_id: twinId,
      twin_label: getTwinName(twinId),
      task: {
        task_type: 'choose_offer',
        offer: {
          name: config.offerType,
          offer_kind: 'upgrade',
          discount_pct: config.discountPct,
          absolute_price_delta: 0,
          constraints: []
        },
        context: {
          flight_length: config.flightLength,
          trip_purpose: config.tripPurpose,
          time_pressure: config.timePressure,
          recent_delays: config.recentDelays
        }
      },
      response: {
        decision: Math.random() > 0.5 ? 'yes' : 'no' as 'yes' | 'no',
        probability: Math.random(),
        rationale: 'Based on the offer and context provided.'
      },
      metadata: {
        timestamp: new Date().toISOString(),
        seed: config.seed
      }
    }
    return {
      conversation_id: conversationId,
      decision
    }
  },

  // Get conversation history
  getHistory: async (
    twinId?: string
  ): Promise<{ conversations: Conversation[]; count: number }> => {
    const params = twinId ? `?twin_id=${twinId}` : ''
    const response = await api.get(`/airline/chat/conversations${params}`)
    return response.data
  },

  // Get specific conversation
  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await api.get(`/airline/chat/conversations/${conversationId}`)
    return response.data
  },

  // Delete conversation
  deleteConversation: async (
    conversationId: string
  ): Promise<{ success: boolean; message: string }> => {
    // For now, just return success since endpoint doesn't exist
    return { success: true, message: 'Conversation deleted' }
  },
}

export default api
