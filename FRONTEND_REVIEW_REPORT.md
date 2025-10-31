# Frontend Codebase Review Report - Darpan Labs MVP

**Date:** October 31, 2025
**Repository:** mvp_v1.0/ui
**Files Analyzed:** 21 TypeScript/TSX files

---

## Executive Summary

The frontend codebase is well-structured with React 18, TypeScript, and modern state management (Zustand). However, several critical issues were identified across error handling, type safety, accessibility, and performance optimization. This report provides a prioritized list of issues with specific locations and recommended fixes.

---

## 1. TYPE SAFETY ISSUES (HIGH PRIORITY)

### 1.1 Unsafe Type Assertions Using `any`
**Severity:** HIGH
**Files Affected:**
- `/ui/src/types/index.ts` (line 47)
- `/ui/src/components/ChatTwinProfile.tsx` (lines 25, 29)
- `/ui/src/components/ChatInterface.tsx` (line 117)
- `/ui/src/components/ChatExperimentPanel.tsx` (line 8)
- `/ui/src/api/client.ts` (lines 63, 77-78)

**Issues:**
```typescript
// Line 47 in types/index.ts
llm_metadata?: any  // Should be properly typed

// Lines 25, 29 in ChatTwinProfile.tsx
const recentExperience = (twin as any).recent_experience || {}
const cohortPriors = (twin as any).cohort_priors || {}
// Should extend AirlineTwin interface with optional fields

// Line 117 in ChatInterface.tsx
const handleRunExperiment = async (experimentConfig: any) => {
// Should be: (experimentConfig: ExperimentConfig)

// Line 8 in ChatExperimentPanel.tsx
onRunExperiment: (config: any) => void
// Should be: (config: ExperimentConfig)

// Lines 63, 77-78 in api/client.ts
export const twinsAPI = {
  exportDecisions: async (format: 'json' | 'csv' = 'json'): Promise<any> => {
  // Return type should be typed

  sendMessage: async (...): Promise<{
    conversation_id: string
    user_message: any
    twin_response: any
  }> => {
```

**Recommendations:**
1. Create specific types for all API responses:
   ```typescript
   interface ChatResponse {
     conversation_id: string
     user_message: ChatMessage
     twin_response: ChatMessage
   }
   ```
2. Extend `AirlineTwin` interface to include optional fields:
   ```typescript
   export interface AirlineTwin {
     // ... existing fields
     recent_experience?: Record<string, number>
     cohort_priors?: {
       price_sensitivity?: 'high' | 'medium' | 'low'
     }
   }
   ```
3. Update all function signatures to use proper types instead of `any`

---

### 1.2 Missing Null/Undefined Safety Checks
**Severity:** MEDIUM
**Files Affected:**
- `/ui/src/components/TwinInsights.tsx` (line 21)
- `/ui/src/components/ResultsAggregated.tsx` (line 62)
- `/ui/src/components/ChatMessage.tsx` (line 20)
- `/ui/src/components/ValidationInfo.tsx` (lines 128, 132, 137, 138, 143, 144, 184, 190, 196, 202)

**Issues:**
```typescript
// Line 21 in TwinInsights.tsx - potential undefined access
const activeTwin = twins.find(t => t.id === activeResult.twin_id)
// Could be undefined but used without null check

// Line 20 in ChatMessage.tsx - potential error with invalid date
const timestamp = new Date(message.timestamp).toLocaleTimeString(...)
// If message.timestamp is invalid, Date constructor won't fail but behavior is undefined

// Lines 128-203 in ValidationInfo.tsx - excessive optional chaining
{datasetInfo.demographics.age?.min}
// Better to destructure safely at top level
```

**Recommendations:**
```typescript
// Safe destructuring
const activeTwin = twins.find(t => t.id === activeResult.twin_id) || null
if (!activeTwin) {
  // Handle missing twin
  return <div>Twin not found</div>
}

// Safe date parsing
const parseTimestamp = (ts: string): string => {
  try {
    return new Date(ts).toLocaleTimeString(...)
  } catch {
    return 'Invalid time'
  }
}
```

---

### 1.3 Incomplete Type Definitions for API Responses
**Severity:** HIGH
**File:** `/ui/src/api/client.ts`

**Issues:**
```typescript
// Line 42-47: batchDecide return type is loosely typed
Promise<{
  results: TwinDecision[]
  errors: { twin_id: string; error: string }[]
  total: number
  successful: number
  failed: number
}>
// Missing: timestamp, metadata, request_id fields commonly in batch APIs
```

**Recommendation:**
```typescript
interface BatchDecideResponse {
  results: TwinDecision[]
  errors: Array<{
    twin_id: string
    error: string
    code?: string
  }>
  total: number
  successful: number
  failed: number
  timestamp: string
  request_id: string
}
```

---

## 2. ERROR HANDLING ISSUES (HIGH PRIORITY)

### 2.1 Unhandled Promise Rejections
**Severity:** HIGH
**Files Affected:**
- `/ui/src/api/client.ts` (all endpoints)
- `/ui/src/components/ExperimentPanel.tsx` (line 15)

**Issues:**
```typescript
// No error handling if axios request fails
export const twinsAPI = {
  getAll: async (): Promise<{ twins: AirlineTwin[]; count: number }> => {
    const response = await api.get('/airline/twins')
    return response.data
    // Network error? Timeout? Not handled!
  },

  batchDecide: async (twinIds: string[], config: ExperimentConfig) => {
    return await twinsAPI.batchDecide(selectedTwinIds, config)
    // If batchDecide throws, entire component fails
  },
}
```

**Recommendations:**
```typescript
export const twinsAPI = {
  getAll: async (): Promise<{ twins: AirlineTwin[]; count: number }> => {
    try {
      const response = await api.get('/airline/twins')
      if (!response.data?.twins || !Array.isArray(response.data.twins)) {
        throw new Error('Invalid response format')
      }
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`Failed to fetch twins: ${error.response?.status} ${error.response?.statusText}`)
      }
      throw error
    }
  },
}
```

---

### 2.2 Silent Failures in useEffect
**Severity:** MEDIUM
**Files Affected:**
- `/ui/src/App.tsx` (line 23)
- `/ui/src/components/ChatInterface.tsx` (line 37)
- `/ui/src/components/ChatSidebar.tsx` (line 26)
- `/ui/src/hooks/useTwinMetrics.ts` (line 26)

**Issues:**
```typescript
// App.tsx - loads twins but errors are only logged
useEffect(() => {
  const loadTwins = async () => {
    try {
      const data = await twinsAPI.getAll()
      setTwins(data.twins)
      selectAllTwins()
    } catch (error) {
      console.error('Failed to load twins:', error)
      setError('Failed to load twins. Make sure the API server is running.')
      // No retry mechanism, component may show empty state forever
    }
  }
  loadTwins()
}, [setTwins, setError, selectAllTwins])
```

**Recommendations:**
```typescript
useEffect(() => {
  let isMounted = true
  const loadTwins = async (retries = 3) => {
    for (let i = 0; i < retries; i++) {
      try {
        const data = await twinsAPI.getAll()
        if (isMounted) {
          setTwins(data.twins)
          selectAllTwins()
          return // Success
        }
      } catch (error) {
        if (i === retries - 1) {
          // Final attempt failed
          if (isMounted) {
            setError('Failed to load twins after 3 retries')
          }
        } else {
          // Retry with exponential backoff
          await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)))
        }
      }
    }
  }
  
  loadTwins()
  return () => { isMounted = false } // Cleanup
}, [setTwins, setError, selectAllTwins])
```

---

### 2.3 Missing Error Boundaries
**Severity:** MEDIUM
**File:** `/ui/src/App.tsx`

**Issues:**
- No Error Boundary component wrapping child components
- If any component crashes, entire app fails
- No graceful degradation

**Recommendation:**
```typescript
// Create ErrorBoundary.tsx
export class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="card bg-red-500/10 p-8">
          <p className="text-red-400">Something went wrong</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

// In App.tsx
<ErrorBoundary>
  <AppContent />
</ErrorBoundary>
```

---

### 2.4 Browser Alert Dialogs (Poor UX)
**Severity:** MEDIUM
**File:** `/ui/src/components/ChatInterface.tsx`

**Issues:**
```typescript
// Lines 111, 119, 160
alert('Failed to send message. Please try again.')
alert('Please start a conversation first')
alert('Failed to run experiment. Please try again.')

// Also in ChatSidebar.tsx, line 48
if (confirm('Delete this conversation?')) {
```

**Recommendations:**
1. Replace alerts with toast notifications:
```typescript
// Install: npm install react-hot-toast
import { toast } from 'react-hot-toast'

// Instead of alert:
toast.error('Failed to send message. Please try again.')
toast.success('Conversation deleted')

// For confirm, use a proper modal:
<ConfirmDialog
  isOpen={showDeleteConfirm}
  title="Delete Conversation"
  message="Are you sure you want to delete this conversation?"
  onConfirm={handleDeleteConversation}
  onCancel={() => setShowDeleteConfirm(false)}
/>
```

---

## 3. PERFORMANCE ISSUES (MEDIUM PRIORITY)

### 3.1 Missing React.memo for Expensive Components
**Severity:** MEDIUM
**Files Affected:**
- `/ui/src/components/TwinCard.tsx` (renders list of twins)
- `/ui/src/components/ChatMessage.tsx` (renders in list)
- `/ui/src/components/ResultsAggregated.tsx` (complex charts)

**Issues:**
```typescript
// TwinCard renders for every parent re-render
export const TwinCard: React.FC<TwinCardProps> = ({ twin }) => {
  // With extensive logic and UI
  const { metrics } = useTwinMetrics() // Called on every render!
  // ...
}

// In TwinSelector, maps over twins array
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {twins.map((twin) => (
    <TwinCard key={twin.id} twin={twin} />
    // No memoization, all TwinCards re-render when any twin changes
  ))}
</div>
```

**Recommendations:**
```typescript
export const TwinCard: React.FC<TwinCardProps> = React.memo(({ twin }) => {
  const { metrics } = useTwinMetrics() // Consider moving to parent
  // ... rest of component
}, (prev, next) => {
  return prev.twin.id === next.twin.id &&
         prev.isSelected === next.isSelected
})

// Better: Optimize the hook
const TwinCard: React.FC<TwinCardProps> = React.memo(({ twin }) => {
  const selectedTwinIds = useStore(state => state.selectedTwinIds)
  const isSelected = selectedTwinIds.includes(twin.id)
  // Metrics already memoized in useTwinMetrics
})
```

---

### 3.2 Multiple API Calls with Hardcoded URLs
**Severity:** MEDIUM
**Files Affected:**
- `/ui/src/components/MetricsPanel.tsx` (line 31)
- `/ui/src/components/CustomerMappingChart.tsx` (line 18)
- `/ui/src/components/ValidationInfo.tsx` (line 36)
- `/ui/src/hooks/useTwinMetrics.ts` (line 40)

**Issues:**
```typescript
// Each component makes its own fetch call
fetch('http://localhost:8000/metrics/validation')
// 4 components = 4 identical network requests!
// No caching between components
```

**Recommendations:**
```typescript
// Create a shared metrics API client
// api/metricsClient.ts
export const metricsAPI = {
  getValidation: async () => {
    const response = await api.get('/metrics/validation')
    return response.data as ValidationMetricsResponse
  }
}

// In App.tsx, load once and share via context or global store
const { data } = useQuery({
  queryKey: ['metrics'],
  queryFn: metricsAPI.getValidation,
  staleTime: 60000, // Cache for 1 minute
})

// Components use the cached data
export const MetricsPanel = () => {
  const { data: metrics } = useQuery({
    queryKey: ['metrics'],
    // Automatically uses cached data!
  })
}
```

---

### 3.3 Missing Lazy Loading for Heavy Components
**Severity:** LOW
**File:** `/ui/src/App.tsx`

**Issues:**
```typescript
// All views loaded upfront even if not shown
<div className="h-[calc(100vh-200px)] grid grid-cols-12 gap-6">
  {viewMode === 'chat' ? (
    <ChatInterface /> // Loaded even if not visible
  ) : viewMode === 'metrics' ? (
    // Metrics components loaded even if not needed
  ) : (
    // Experiment view
  )}
</div>
```

**Recommendations:**
```typescript
import { lazy, Suspense } from 'react'

const ChatInterface = lazy(() => import('./components/ChatInterface'))
const MetricsView = lazy(() => import('./components/MetricsView'))
const ExperimentView = lazy(() => import('./components/ExperimentView'))

export default function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      {viewMode === 'chat' && <ChatInterface />}
      {viewMode === 'metrics' && <MetricsView />}
      {viewMode === 'experiment' && <ExperimentView />}
    </Suspense>
  )
}
```

---

## 4. CODE QUALITY ISSUES (MEDIUM PRIORITY)

### 4.1 Duplicate Code - Chat Message Handling
**Severity:** MEDIUM
**File:** `/ui/src/components/ChatInterface.tsx`

**Issues:**
```typescript
// Lines 71-75 and 98-107 - Similar conversation update logic duplicated
// addConversation and updateConversation have similar structure
setCurrentMessages((prev) => [
  ...prev,
  response.user_message,
  response.twin_response,
])

// Similar spread operations repeated throughout
const updatedConv: Conversation = {
  ...existingConv,
  messages: [...existingConv.messages, ...newMessages],
  updated_at: new Date().toISOString(),
  message_count: (existingConv.message_count || 0) + newMessageCount,
}
```

**Recommendations:**
```typescript
// Extract to utility function
function createUpdatedConversation(
  existing: Conversation,
  newMessages: ChatMessage[]
): Conversation {
  return {
    ...existing,
    messages: [...existing.messages, ...newMessages],
    updated_at: new Date().toISOString(),
    message_count: (existing.message_count || 0) + newMessages.length,
  }
}

// Reuse in both places
const updatedConv = createUpdatedConversation(existingConv, [
  response.user_message,
  response.twin_response
])
updateConversation(updatedConv)
```

---

### 4.2 Complex Component with Mixed Concerns
**Severity:** MEDIUM
**File:** `/ui/src/components/ChatInterface.tsx`

**Issues:**
- Component handles: state management, message sending, experiments, keyboard handlers, rendering
- 300+ lines with multiple responsibilities
- Hard to test, maintain, and debug

**Recommendations:**
```typescript
// Split into smaller components
// ChatMessageList.tsx - renders messages only
export const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages, twinId }) => {
  // Just render, no logic
}

// ChatInputForm.tsx - handles input and sending
export const ChatInputForm: React.FC<ChatInputFormProps> = ({ onSend, disabled }) => {
  // Just form handling
}

// useChat.ts - custom hook for chat logic
export const useChat = (twinId: string) => {
  // All chat business logic
}

// ChatInterface.tsx - orchestrates
export const ChatInterface: React.FC = () => {
  const { messages, sendMessage } = useChat(activeChatTwinId)
  
  return (
    <>
      <ChatMessageList messages={messages} />
      <ChatInputForm onSend={sendMessage} />
    </>
  )
}
```

---

### 4.3 Hardcoded Values and Magic Numbers
**Severity:** LOW
**Files Affected:**
- `/ui/src/components/ExperimentPanel.tsx` (lines 68, 70)
- `/ui/src/components/ChatExperimentPanel.tsx` (lines 79, 79)
- `/ui/src/components/CustomerMappingChart.tsx` (line 56)
- `/ui/src/components/TwinSelector.tsx` (line 37)

**Issues:**
```typescript
// ExperimentPanel.tsx
<input
  type="range"
  min="0"
  max="0.5"  // Magic number
  step="0.05"
  // Why 0.5? Should be a constant

// ChatExperimentPanel.tsx
max="1" // Different from above!

// CustomerMappingChart.tsx
const percentage = (twin.customer_count / 400) * 100 // Where does 400 come from?

// TwinSelector.tsx
<div className="max-h-[600px]"> // Magic dimension
```

**Recommendations:**
```typescript
// Create constants file: ui/src/constants/config.ts
export const DISCOUNT_CONFIG = {
  MIN: 0,
  MAX: 0.5,
  STEP: 0.05,
} as const

export const CHAT_EXPERIMENT_DISCOUNT = {
  MIN: 0,
  MAX: 1,
  STEP: 0.05,
} as const

export const DATASET_CONFIG = {
  TOTAL_SAMPLES: 400,
  TWIN_LIST_MAX_HEIGHT_PX: 600,
} as const

// Usage:
<input
  max={DISCOUNT_CONFIG.MAX}
  step={DISCOUNT_CONFIG.STEP}
/>
```

---

### 4.4 Missing PropTypes/Interface Validation
**Severity:** MEDIUM
**File:** `/ui/src/components/ChatExperimentPanel.tsx`

**Issues:**
```typescript
interface ChatExperimentPanelProps {
  isOpen: boolean
  onClose: () => void
  onRunExperiment: (config: any) => void // any!
}

// No validation of localConfig before submitting
const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  onRunExperiment(localConfig) // What if localConfig is invalid?
}
```

**Recommendations:**
```typescript
// Use zod for runtime validation
import { z } from 'zod'

const ExperimentConfigSchema = z.object({
  offerType: z.enum(['legroom', 'wifi', 'lounge', 'boarding', 'baggage']),
  discountPct: z.number().min(0).max(1),
  flightLength: z.enum(['short', 'medium', 'long']),
  tripPurpose: z.enum(['business', 'leisure']),
  timePressure: z.enum(['low', 'medium', 'high']),
  recentDelays: z.enum(['none', 'minor', 'major']),
})

const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  const result = ExperimentConfigSchema.safeParse(localConfig)
  if (!result.success) {
    setError('Invalid configuration')
    return
  }
  onRunExperiment(result.data)
}
```

---

## 5. ACCESSIBILITY ISSUES (MEDIUM PRIORITY)

### 5.1 Missing ARIA Labels and Semantic HTML
**Severity:** MEDIUM
**Files Affected:** All components

**Issues:**
```typescript
// Buttons with no aria-labels
<button onClick={selectAllTwins}>Select All</button>
// Good for visual users, but screen readers see nothing

// Icons without context
<Users className="text-neon-green" size={24} />
// What does this represent for assistive tech?

// Images in cards without alt text
<div className="w-12 h-12 rounded-full flex items-center justify-center">
  {twinName.charAt(0)}
</div>
// This is a visual indicator, not text

// Form inputs without labels
<input
  type="range"
  // No aria-label or associated <label>
/>
```

**Recommendations:**
```typescript
// Add aria labels
<button
  onClick={selectAllTwins}
  aria-label="Select all twins for experiment"
  title="Select all twins"
>
  Select All
</button>

// Icon with descriptive aria-label
<Users
  className="text-neon-green"
  size={24}
  aria-label="Number of customers"
  role="img"
/>

// Form inputs with proper labels
<div>
  <label htmlFor="discount-slider">
    Discount: <span aria-live="polite">{(discountPct * 100).toFixed(0)}%</span>
  </label>
  <input
    id="discount-slider"
    type="range"
    aria-labelledby="discount-slider"
    aria-valuenow={discountPct}
    aria-valuemin={0}
    aria-valuemax={0.5}
  />
</div>
```

---

### 5.2 Keyboard Navigation
**Severity:** LOW
**Files Affected:**
- `/ui/src/components/TwinSelector.tsx` - grid not keyboard navigable
- `/ui/src/components/ChatSidebar.tsx` - nested buttons not fully accessible
- `/ui/src/components/ExperimentPanel.tsx` - form could use better tab order

**Recommendations:**
```typescript
// Ensure buttons are properly focusable
<button
  onClick={() => {}}
  tabIndex={-1} // Should be 0 or removed
  // Never use negative tabIndex for interactive elements
/>

// Use keyboard event handlers
<div
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleSelection()
    }
  }}
  role="button"
  tabIndex={0}
/>

// Better: use actual button element
<button onClick={handleSelection}>
  Select Twin
</button>
```

---

### 5.3 Color Contrast Issues
**Severity:** MEDIUM
**File:** `/ui/src/components/TwinCard.tsx`

**Issues:**
```typescript
// Line 33
className="bg-neon-surfacelight text-neon-green"
// Need to verify contrast ratio >= 4.5:1 for normal text

// Line 128
<span className="ml-1 text-neon-text font-medium">{twin.demographics.age_band}</span>
// text-neon-text on default background - check ratio
```

**Recommendations:**
```typescript
// Test colors for contrast ratio
// Use tools: WebAIM Contrast Checker, Deque axe DevTools

// For better accessibility, increase color brightness
// Current: neon-green #B8FF00
// Against: neon-surface #0F0F1E
// Ratio might be < 4.5:1

// Solution: Use darker green or lighter background
// Or use explicit background color
<span className="bg-neon-surfacelight text-neon-text font-medium">
  {twin.demographics.age_band}
</span>
```

---

## 6. BEST PRACTICES ISSUES (MEDIUM PRIORITY)

### 6.1 useEffect Dependencies
**Severity:** MEDIUM
**File:** `/ui/src/components/ChatInterface.tsx`

**Issues:**
```typescript
// Lines 52-54 - missing dependency
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
}, [currentMessages]) // OK but could be optimized

// Lines 35-49 - Missing cleanup for race conditions
useEffect(() => {
  if (activeConversationId) {
    const loadConversation = async () => {
      try {
        const conv = await chatAPI.getConversation(activeConversationId)
        setCurrentMessages(conv.messages)
      } catch (error) {
        console.error('Failed to load conversation:', error)
      }
    }
    loadConversation()
  } else {
    setCurrentMessages([])
  }
}, [activeConversationId])
// If component unmounts while loading, setCurrentMessages still called (memory leak)
```

**Recommendations:**
```typescript
useEffect(() => {
  if (!activeConversationId) {
    setCurrentMessages([])
    return
  }

  let isMounted = true

  const loadConversation = async () => {
    try {
      const conv = await chatAPI.getConversation(activeConversationId)
      if (isMounted) { // Check before state update
        setCurrentMessages(conv.messages)
      }
    } catch (error) {
      if (isMounted) {
        console.error('Failed to load conversation:', error)
      }
    }
  }

  loadConversation()

  return () => {
    isMounted = false // Cleanup
  }
}, [activeConversationId])
```

---

### 6.2 Global State Mutation Pattern
**Severity:** LOW
**File:** `/ui/src/store/useStore.ts`

**Issues:**
```typescript
// While the store is well-designed, the chat actions could be more atomic
addConversation: (conversation) => set((state) => ({
  conversations: [conversation, ...state.conversations],
})),

// What if conversation already exists? Could create duplicates
// No upsert pattern

removeConversation: (conversationId) => set((state) => ({
  conversations: state.conversations.filter((conv) => conv.id !== conversationId),
})),
// What if it doesn't exist? Silent failure is OK here, but document it
```

**Recommendations:**
```typescript
// Add helper function to prevent duplicates
addConversation: (conversation) => set((state) => {
  const exists = state.conversations.some(c => c.id === conversation.id)
  if (exists) {
    return {} // No change
  }
  return {
    conversations: [conversation, ...state.conversations],
  }
}),

// Add upsert for conversation updates
upsertConversation: (conversation) => set((state) => ({
  conversations: state.conversations.some(c => c.id === conversation.id)
    ? state.conversations.map(c => c.id === conversation.id ? conversation : c)
    : [conversation, ...state.conversations],
})),
```

---

### 6.3 Console Statements Left in Production Code
**Severity:** LOW
**Files Affected:**
- `/ui/src/hooks/useTwinMetrics.ts` (line 55)
- `/ui/src/App.tsx` (line 29)
- `/ui/src/components/CustomerMappingChart.tsx` (line 25)
- `/ui/src/components/ChatSidebar.tsx` (lines 31, 56)
- `/ui/src/components/ChatInterface.tsx` (lines 42, 110, 159)
- `/ui/src/components/MetricsPanel.tsx` (line 38)
- `/ui/src/components/ValidationInfo.tsx` (line 43)

**Issues:**
```typescript
console.error('Failed to load conversation:', error)
// Good for development, but should use proper logging in production
```

**Recommendations:**
```typescript
// Create logger utility: ui/src/utils/logger.ts
export const logger = {
  error: (message: string, error?: any) => {
    if (import.meta.env.DEV) {
      console.error(message, error)
    }
    // In production: send to error tracking (Sentry, etc.)
    if (import.meta.env.PROD) {
      reportError(message, error)
    }
  },
  warn: (message: string) => {
    if (import.meta.env.DEV) console.warn(message)
  }
}

// Usage:
catch (error) {
  logger.error('Failed to load conversation', error)
}
```

---

### 6.4 No Error Recovery Mechanism
**Severity:** MEDIUM
**Files Affected:**
- `/ui/src/components/MetricsPanel.tsx` (line 32)
- `/ui/src/components/ValidationInfo.tsx` (line 36)
- `/ui/src/components/CustomerMappingChart.tsx` (line 18)

**Issues:**
```typescript
// Once fetch fails, shows "Failed to load" forever
if (!metrics) {
  return (
    <div className="card">
      <p className="text-neon-textsecondary">Failed to load metrics</p>
    </div>
  )
}
// No retry button, no way for user to recover
```

**Recommendations:**
```typescript
export const MetricsPanel: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadMetrics = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/metrics/validation')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMetrics()
  }, [])

  if (error) {
    return (
      <div className="card bg-red-500/10">
        <p className="text-red-400">{error}</p>
        <button
          onClick={loadMetrics}
          className="btn-primary mt-2"
        >
          Retry
        </button>
      </div>
    )
  }
  // ...
}
```

---

## 7. SUMMARY TABLE - PRIORITIZED ISSUES

| Priority | Category | Count | Files | Impact |
|----------|----------|-------|-------|--------|
| HIGH | Type Safety - `any` types | 6 | 5 files | Crashes at runtime, hard to debug |
| HIGH | Error Handling - Unhandled rejections | 8+ | 7 files | App may hang or crash silently |
| MEDIUM | Performance - No memoization | 3 | 3 files | Unnecessary re-renders, lag |
| MEDIUM | Accessibility - Missing ARIA | 10+ | All | Unusable for screen readers |
| MEDIUM | Error Handling - Silent failures | 4 | 4 files | User confusion, no feedback |
| MEDIUM | Code Quality - Complex components | 2 | 2 files | Hard to maintain and test |
| MEDIUM | Best Practices - useEffect cleanup | 2 | 2 files | Memory leaks, race conditions |
| LOW | Code Quality - Hardcoded values | 6 | 4 files | Hard to maintain |
| LOW | UX - Alert dialogs | 3 | 2 files | Poor user experience |

---

## 8. RECOMMENDED FIXES TIMELINE

**Phase 1 (Critical - Week 1):**
1. Add Error Boundary component
2. Fix unsafe `any` types in API client
3. Add proper error handling to all fetch calls
4. Replace alert dialogs with toast notifications

**Phase 2 (Important - Week 2):**
1. Add ARIA labels to all interactive elements
2. Create logger utility to remove console statements
3. Add retry mechanisms with user feedback
4. Refactor complex components using custom hooks

**Phase 3 (Enhancement - Week 3):**
1. Add React.memo to expensive components
2. Consolidate duplicate API calls with React Query
3. Create constants configuration file
4. Add input validation with zod

**Phase 4 (Polish - Week 4):**
1. Implement lazy loading for views
2. Add comprehensive accessibility testing
3. Optimize bundle size
4. Set up error tracking (Sentry)

---

## 9. TESTING RECOMMENDATIONS

Add these test suites:
1. **Unit Tests**: Type safety, utility functions
2. **Integration Tests**: API client, hooks
3. **E2E Tests**: User workflows (experiment, chat)
4. **Accessibility Tests**: axe DevTools, screen reader testing
5. **Performance Tests**: Core Web Vitals, Lighthouse

---

## 10. TOOLS TO IMPLEMENT

1. **ESLint**: Catch type issues early
   ```bash
   npm install --save-dev eslint @typescript-eslint/eslint-plugin
   ```

2. **Prettier**: Code formatting consistency
   ```bash
   npm install --save-dev prettier
   ```

3. **React Testing Library**: Component testing
   ```bash
   npm install --save-dev @testing-library/react
   ```

4. **Zod**: Runtime validation
   ```bash
   npm install zod
   ```

5. **React Hot Toast**: Better notifications
   ```bash
   npm install react-hot-toast
   ```

6. **Sentry**: Error tracking (production)
   ```bash
   npm install @sentry/react
   ```

---

## Conclusion

The codebase has a solid foundation with React 18, TypeScript, and Zustand. The main issues are:
1. **Type safety gaps** using `any` instead of proper types
2. **Missing error handling** for network failures
3. **Accessibility gaps** preventing assistive technology use
4. **Performance optimizations** needed for larger datasets

Implementing the recommended fixes will significantly improve code quality, reliability, and user experience. Start with Phase 1 (Critical items) which can be completed in 1 week.

