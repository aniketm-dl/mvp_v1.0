import axios from 'axios'
import type { AirlineTwin, TwinDecision, ExperimentConfig, Conversation, ChatExperimentResult } from '../types'

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
    const response = await api.post('/airline/chat', {
      twin_id: twinId,
      message,
      conversation_id: conversationId,
    })
    return response.data
  },

  // Run experiment within chat
  runExperiment: async (
    twinId: string,
    conversationId: string,
    config: ExperimentConfig
  ): Promise<ChatExperimentResult> => {
    const response = await api.post('/airline/chat/experiment', {
      twin_id: twinId,
      conversation_id: conversationId,
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

  // Get conversation history
  getHistory: async (
    twinId?: string
  ): Promise<{ conversations: Conversation[]; count: number }> => {
    const url = twinId
      ? `/airline/chat/history?twin_id=${twinId}`
      : '/airline/chat/history'
    const response = await api.get(url)
    return response.data
  },

  // Get specific conversation
  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await api.get(`/airline/chat/conversation/${conversationId}`)
    return response.data
  },

  // Delete conversation
  deleteConversation: async (
    conversationId: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/airline/chat/conversation/${conversationId}`)
    return response.data
  },
}

export default api
