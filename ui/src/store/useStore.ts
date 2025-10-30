import { create } from 'zustand'
import type { AirlineTwin, TwinDecision, ExperimentConfig, ViewMode, Conversation, ChatMessage } from '../types'

interface AppState {
  // Twins data
  twins: AirlineTwin[]
  selectedTwinIds: string[]

  // Experiment results
  results: TwinDecision[]
  isLoading: boolean
  error: string | null

  // Experiment configuration
  config: ExperimentConfig

  // View mode
  viewMode: ViewMode

  // Chat state
  activeChatTwinId: string | null
  activeConversationId: string | null
  conversations: Conversation[]
  chatLoading: boolean

  // Actions
  setTwins: (twins: AirlineTwin[]) => void
  setSelectedTwinIds: (ids: string[]) => void
  toggleTwinSelection: (id: string) => void
  selectAllTwins: () => void
  clearSelection: () => void

  setResults: (results: TwinDecision[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  updateConfig: (config: Partial<ExperimentConfig>) => void

  setViewMode: (mode: ViewMode) => void

  // Chat actions
  setActiveChatTwin: (twinId: string | null) => void
  setActiveConversation: (conversationId: string | null) => void
  setConversations: (conversations: Conversation[]) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (conversation: Conversation) => void
  removeConversation: (conversationId: string) => void
  setChatLoading: (loading: boolean) => void
  startNewChat: (twinId: string) => void
}

export const useStore = create<AppState>((set, get) => ({
  // Initial state
  twins: [],
  selectedTwinIds: [],
  results: [],
  isLoading: false,
  error: null,
  config: {
    offerType: 'legroom',
    discountPct: 0.20,
    flightLength: 'medium',
    tripPurpose: 'business',
    timePressure: 'medium',
    recentDelays: 'minor',
    seed: 42,
  },
  viewMode: 'experiment',

  // Chat state
  activeChatTwinId: null,
  activeConversationId: null,
  conversations: [],
  chatLoading: false,

  // Actions
  setTwins: (twins) => set({ twins }),

  setSelectedTwinIds: (ids) => set({ selectedTwinIds: ids }),

  toggleTwinSelection: (id) => set((state) => {
    const isSelected = state.selectedTwinIds.includes(id)
    return {
      selectedTwinIds: isSelected
        ? state.selectedTwinIds.filter((tid) => tid !== id)
        : [...state.selectedTwinIds, id],
    }
  }),

  selectAllTwins: () => set((state) => ({
    selectedTwinIds: state.twins.map((t) => t.id),
  })),

  clearSelection: () => set({ selectedTwinIds: [] }),

  setResults: (results) => set({ results }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  updateConfig: (configUpdate) => set((state) => ({
    config: { ...state.config, ...configUpdate },
  })),

  setViewMode: (mode) => set({ viewMode: mode }),

  // Chat actions
  setActiveChatTwin: (twinId) => set({ activeChatTwinId: twinId }),

  setActiveConversation: (conversationId) => set({ activeConversationId: conversationId }),

  setConversations: (conversations) => set({ conversations }),

  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations],
  })),

  updateConversation: (conversation) => set((state) => ({
    conversations: state.conversations.map((conv) =>
      conv.id === conversation.id ? conversation : conv
    ),
  })),

  removeConversation: (conversationId) => set((state) => ({
    conversations: state.conversations.filter((conv) => conv.id !== conversationId),
  })),

  setChatLoading: (loading) => set({ chatLoading: loading }),

  startNewChat: (twinId) => set({
    activeChatTwinId: twinId,
    activeConversationId: null,
  }),
}))
