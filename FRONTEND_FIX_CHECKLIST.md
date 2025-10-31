# Frontend Code Review - Fix Checklist

## Phase 1: Critical Type Safety & Error Handling (Week 1)

### Type Safety Fixes
- [ ] `/ui/src/types/index.ts` - Line 47: Replace `llm_metadata?: any` with specific type
  ```typescript
  llm_metadata?: {
    temperature?: number
    top_p?: number
    provider?: string
  }
  ```

- [ ] `/ui/src/api/client.ts` - Line 63: Fix exportDecisions return type
  ```typescript
  Promise<ExportResponse> // Create this interface
  ```

- [ ] `/ui/src/api/client.ts` - Lines 77-78: Fix sendMessage return type
  ```typescript
  Promise<ChatResponse> // Create this interface
  ```

- [ ] `/ui/src/components/ChatTwinProfile.tsx` - Lines 25, 29: Remove `as any`
  ```typescript
  // Add to AirlineTwin interface:
  recent_experience?: Record<string, number>
  cohort_priors?: { price_sensitivity?: string }
  ```

- [ ] `/ui/src/components/ChatInterface.tsx` - Line 117: Fix handleRunExperiment param
  ```typescript
  const handleRunExperiment = async (experimentConfig: ExperimentConfig) => {
  ```

- [ ] `/ui/src/components/ChatExperimentPanel.tsx` - Line 8: Fix onRunExperiment type
  ```typescript
  onRunExperiment: (config: ExperimentConfig) => void
  ```

### Error Handling - API Client
- [ ] `/ui/src/api/client.ts` - Add try-catch to getAll()
  ```typescript
  try {
    const response = await api.get('/airline/twins')
    if (!response.data?.twins || !Array.isArray(response.data.twins)) {
      throw new Error('Invalid response format')
    }
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`HTTP ${error.response?.status}`)
    }
    throw error
  }
  ```

- [ ] `/ui/src/api/client.ts` - Add try-catch to decide()
- [ ] `/ui/src/api/client.ts` - Add try-catch to batchDecide()
- [ ] `/ui/src/api/client.ts` - Add try-catch to sendMessage()
- [ ] `/ui/src/api/client.ts` - Add try-catch to runExperiment()
- [ ] `/ui/src/api/client.ts` - Add try-catch to getHistory()
- [ ] `/ui/src/api/client.ts` - Add try-catch to getConversation()
- [ ] `/ui/src/api/client.ts` - Add try-catch to deleteConversation()

### Error Boundaries
- [ ] Create `/ui/src/components/ErrorBoundary.tsx`
  ```typescript
  export class ErrorBoundary extends React.Component {
    state = { hasError: false, error: null }
    
    static getDerivedStateFromError(error: Error) {
      return { hasError: true, error }
    }
    
    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      console.error('Error caught:', error, errorInfo)
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
  ```

- [ ] `/ui/src/App.tsx` - Wrap AppContent with ErrorBoundary

### Alert Dialog Replacement
- [ ] Install: `npm install react-hot-toast`
- [ ] Create `/ui/src/utils/notifications.ts`:
  ```typescript
  import { toast } from 'react-hot-toast'
  
  export const notify = {
    error: (message: string) => toast.error(message),
    success: (message: string) => toast.success(message),
    loading: (message: string) => toast.loading(message),
  }
  ```

- [ ] `/ui/src/components/ChatInterface.tsx` - Line 111: Replace alert with toast
  ```typescript
  notify.error('Failed to send message. Please try again.')
  ```

- [ ] `/ui/src/components/ChatInterface.tsx` - Line 119: Replace alert with toast
  ```typescript
  notify.error('Please start a conversation first')
  ```

- [ ] `/ui/src/components/ChatInterface.tsx` - Line 160: Replace alert with toast

- [ ] `/ui/src/components/ChatSidebar.tsx` - Line 48: Replace confirm with modal
  ```typescript
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  // Use ConfirmDialog component or state + modal
  ```

### useEffect Cleanup
- [ ] `/ui/src/components/ChatInterface.tsx` - Lines 35-49: Add cleanup
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
        if (isMounted) {
          setCurrentMessages(conv.messages)
        }
      } catch (error) {
        if (isMounted) {
          console.error('Failed to load conversation:', error)
        }
      }
    }
    
    loadConversation()
    
    return () => { isMounted = false }
  }, [activeConversationId])
  ```

- [ ] `/ui/src/App.tsx` - Lines 20-34: Add cleanup and retry
- [ ] `/ui/src/components/ChatSidebar.tsx` - Lines 25-35: Add cleanup

---

## Phase 2: Null Safety & Performance (Week 2)

### Null/Undefined Checks
- [ ] `/ui/src/components/TwinInsights.tsx` - Line 21: Add null check
  ```typescript
  const activeTwin = twins.find(t => t.id === activeResult.twin_id)
  if (!activeTwin) {
    return <div className="card">Twin not found</div>
  }
  ```

- [ ] `/ui/src/components/ChatMessage.tsx` - Line 20: Safe date parsing
  ```typescript
  const parseTimestamp = (ts: string): string => {
    try {
      return new Date(ts).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
      })
    } catch {
      return 'Invalid time'
    }
  }
  const timestamp = parseTimestamp(message.timestamp)
  ```

- [ ] `/ui/src/components/ValidationInfo.tsx` - Lines 128-203: Safe optional chaining
  ```typescript
  const ageStats = datasetInfo?.demographics?.age
  if (!ageStats) return null
  // Then safely use ageStats.min, ageStats.max, etc.
  ```

- [ ] `/ui/src/components/ResultsAggregated.tsx` - Line 62: Safe destructuring
  ```typescript
  if (!aggregatedData) return null // Already checked at line 51
  const { acceptanceRate, avgProbability, chartData, yesCount, noCount } = aggregatedData
  ```

### React.memo Optimization
- [ ] `/ui/src/components/TwinCard.tsx` - Wrap with React.memo
  ```typescript
  export const TwinCard = React.memo(({ twin }: TwinCardProps) => {
    // ... component code
  }, (prev, next) => {
    return prev.twin.id === next.twin.id &&
           prev.isSelected === next.isSelected
  })
  ```

- [ ] `/ui/src/components/ChatMessage.tsx` - Wrap with React.memo
  ```typescript
  export const ChatMessage = React.memo(({ message, twinId, isExperiment, experimentResult }: ChatMessageProps) => {
    // ... component code
  })
  ```

- [ ] Optimize useTwinMetrics hook - move to component level
  ```typescript
  // In TwinCard, use Zustand selector instead
  const selectedTwinIds = useStore(state => state.selectedTwinIds)
  const metrics = useStore(state => state.metrics) // Add to store
  ```

### Consolidate Duplicate API Calls
- [ ] Create `/ui/src/api/metricsClient.ts`:
  ```typescript
  export const metricsAPI = {
    getValidation: async () => {
      const response = await api.get('/metrics/validation')
      return response.data
    }
  }
  ```

- [ ] `/ui/src/components/MetricsPanel.tsx` - Replace fetch with api client + React Query
  ```typescript
  import { useQuery } from '@tanstack/react-query'
  import { metricsAPI } from '../api/metricsClient'
  
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['metrics'],
    queryFn: metricsAPI.getValidation,
    staleTime: 60000,
  })
  ```

- [ ] `/ui/src/components/ValidationInfo.tsx` - Update to use React Query
- [ ] `/ui/src/components/CustomerMappingChart.tsx` - Update to use React Query
- [ ] `/ui/src/hooks/useTwinMetrics.ts` - Update to use React Query

### Silent Failure Fixes
- [ ] `/ui/src/App.tsx` - Add retry mechanism
  ```typescript
  const loadTwins = async (retries = 3) => {
    for (let i = 0; i < retries; i++) {
      try {
        // ...
        return // Success
      } catch (error) {
        if (i === retries - 1) {
          setError('Failed to load twins after 3 retries')
        } else {
          await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)))
        }
      }
    }
  }
  ```

- [ ] `/ui/src/components/MetricsPanel.tsx` - Add error retry
  ```typescript
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
  
  // In render:
  if (error) {
    return (
      <div className="card bg-red-500/10">
        <p className="text-red-400">{error}</p>
        <button onClick={loadMetrics} className="btn-primary mt-2">
          Retry
        </button>
      </div>
    )
  }
  ```

- [ ] `/ui/src/components/ValidationInfo.tsx` - Add error retry
- [ ] `/ui/src/components/CustomerMappingChart.tsx` - Add error retry

---

## Phase 3: Accessibility & Code Quality (Week 3)

### Create Constants File
- [ ] Create `/ui/src/constants/config.ts`:
  ```typescript
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
  
  export const UI_CONFIG = {
    CACHE_DURATION_MS: 60000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY_MS: 1000,
  } as const
  ```

- [ ] `/ui/src/components/ExperimentPanel.tsx` - Use DISCOUNT_CONFIG
  ```typescript
  <input
    type="range"
    min={DISCOUNT_CONFIG.MIN}
    max={DISCOUNT_CONFIG.MAX}
    step={DISCOUNT_CONFIG.STEP}
  />
  ```

- [ ] `/ui/src/components/ChatExperimentPanel.tsx` - Use CHAT_EXPERIMENT_DISCOUNT
- [ ] `/ui/src/components/CustomerMappingChart.tsx` - Use DATASET_CONFIG

### Create Logger Utility
- [ ] Create `/ui/src/utils/logger.ts`:
  ```typescript
  export const logger = {
    error: (message: string, error?: any) => {
      if (import.meta.env.DEV) {
        console.error(message, error)
      }
      // TODO: Add Sentry reporting in production
    },
    warn: (message: string) => {
      if (import.meta.env.DEV) {
        console.warn(message)
      }
    },
    info: (message: string) => {
      if (import.meta.env.DEV) {
        console.log(message)
      }
    }
  }
  ```

- [ ] Replace all `console.error` with `logger.error`:
  - `/ui/src/hooks/useTwinMetrics.ts` - Line 55
  - `/ui/src/App.tsx` - Line 29
  - `/ui/src/components/CustomerMappingChart.tsx` - Line 25
  - `/ui/src/components/ChatSidebar.tsx` - Lines 31, 56
  - `/ui/src/components/ChatInterface.tsx` - Lines 42, 110, 159
  - `/ui/src/components/MetricsPanel.tsx` - Line 38
  - `/ui/src/components/ValidationInfo.tsx` - Line 43

### Accessibility - ARIA Labels
- [ ] `/ui/src/components/TwinSelector.tsx`:
  ```typescript
  <button
    onClick={selectAllTwins}
    aria-label="Select all twins for experiment"
    title="Select all twins"
  >
    Select All
  </button>
  
  <button
    onClick={clearSelection}
    aria-label="Clear all selections"
  >
    Clear
  </button>
  ```

- [ ] `/ui/src/components/ExperimentPanel.tsx`:
  ```typescript
  <input
    type="range"
    aria-label="Discount percentage"
    aria-valuenow={config.discountPct}
    aria-valuemin={0}
    aria-valuemax={0.5}
    aria-valuetext={`${(config.discountPct * 100).toFixed(0)}%`}
  />
  ```

- [ ] `/ui/src/components/TwinCard.tsx` - Add aria-labels to all interactive elements
- [ ] `/ui/src/components/ChatInterface.tsx` - Add aria-labels to buttons
- [ ] `/ui/src/components/ChatSidebar.tsx` - Add aria-labels to conversation items
- [ ] `/ui/src/components/Header.tsx` - Add aria-labels to nav buttons

### Accessibility - Semantic HTML
- [ ] Replace non-semantic `<div>` with buttons/labels where appropriate
- [ ] Add `<main>` tag wrapper in App.tsx (already has it, good)
- [ ] Add `<nav>` tags where needed
- [ ] Use `<form>` elements in ExperimentPanel.tsx

### Refactor ChatInterface Component
- [ ] Create `/ui/src/components/ChatMessageList.tsx`:
  ```typescript
  export interface ChatMessageListProps {
    messages: ChatMessage[]
    twinId?: string
  }
  
  export const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages, twinId }) => {
    const messagesEndRef = useRef<HTMLDivElement>(null)
    
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])
    
    return (
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} twinId={twinId} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    )
  }
  ```

- [ ] Create `/ui/src/components/ChatInputForm.tsx`:
  ```typescript
  export interface ChatInputFormProps {
    onSend: (message: string) => void
    disabled: boolean
    twinName?: string
  }
  
  export const ChatInputForm: React.FC<ChatInputFormProps> = ({
    onSend,
    disabled,
    twinName = 'Twin'
  }) => {
    const [inputMessage, setInputMessage] = useState('')
    
    const handleSubmit = () => {
      if (inputMessage.trim()) {
        onSend(inputMessage.trim())
        setInputMessage('')
      }
    }
    
    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    }
    
    return (
      <div className="p-4 border-t border-neon-surfacelight flex gap-3">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={`Message ${twinName}...`}
          className="input flex-1 resize-none"
          rows={2}
          disabled={disabled}
          aria-label={`Message input for ${twinName}`}
        />
        <button
          onClick={handleSubmit}
          disabled={!inputMessage.trim() || disabled}
          className="btn-primary px-4 h-auto disabled:opacity-50"
          aria-label="Send message"
        >
          {disabled ? <Loader2 /> : <Send />}
        </button>
      </div>
    )
  }
  ```

- [ ] Create `/ui/src/hooks/useChat.ts`:
  ```typescript
  export const useChat = (twinId: string | null) => {
    const [currentMessages, setCurrentMessages] = useState<ChatMessage[]>([])
    const { activeConversationId, setActiveConversation, conversations, addConversation, updateConversation } = useStore()
    
    const sendMessage = async (userMessage: string) => {
      if (!twinId) return
      
      try {
        const response = await chatAPI.sendMessage(twinId, userMessage, activeConversationId || undefined)
        setCurrentMessages(prev => [...prev, response.user_message, response.twin_response])
        
        if (!activeConversationId) {
          setActiveConversation(response.conversation_id)
          addConversation({
            id: response.conversation_id,
            twin_id: twinId,
            messages: [response.user_message, response.twin_response],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            preview: userMessage,
            message_count: 2,
          })
        } else {
          const existingConv = conversations.find(c => c.id === activeConversationId)
          if (existingConv) {
            updateConversation({
              ...existingConv,
              messages: [...existingConv.messages, response.user_message, response.twin_response],
              updated_at: new Date().toISOString(),
              message_count: (existingConv.message_count || 0) + 2,
            })
          }
        }
      } catch (error) {
        logger.error('Failed to send message', error)
        notify.error('Failed to send message')
        throw error
      }
    }
    
    return { currentMessages, sendMessage, setCurrentMessages }
  }
  ```

- [ ] Simplify `/ui/src/components/ChatInterface.tsx` using new components

---

## Phase 4: Polish & Testing (Week 4)

### Input Validation
- [ ] Install: `npm install zod`
- [ ] Create `/ui/src/schemas/experiment.ts`:
  ```typescript
  import { z } from 'zod'
  
  export const ExperimentConfigSchema = z.object({
    offerType: z.enum(['legroom', 'wifi', 'lounge', 'boarding', 'baggage']),
    discountPct: z.number().min(0).max(1),
    flightLength: z.enum(['short', 'medium', 'long']),
    tripPurpose: z.enum(['business', 'leisure']),
    timePressure: z.enum(['low', 'medium', 'high']),
    recentDelays: z.enum(['none', 'minor', 'major']),
    seed: z.number().optional(),
  })
  ```

- [ ] `/ui/src/components/ChatExperimentPanel.tsx` - Add validation
  ```typescript
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const result = ExperimentConfigSchema.safeParse(localConfig)
    if (!result.success) {
      notify.error('Invalid configuration')
      return
    }
    onRunExperiment(result.data)
    onClose()
  }
  ```

### Testing Setup
- [ ] Install: `npm install --save-dev @testing-library/react @testing-library/jest-dom vitest`
- [ ] Create `/ui/src/__tests__/api/client.test.ts`
- [ ] Create `/ui/src/__tests__/components/TwinCard.test.tsx`
- [ ] Create `/ui/src/__tests__/hooks/useChat.test.ts`
- [ ] Create `/ui/src/__tests__/schemas/experiment.test.ts`

### Linting & Formatting
- [ ] Install: `npm install --save-dev eslint @typescript-eslint/eslint-plugin prettier eslint-plugin-jsx-a11y`
- [ ] Create `.eslintrc.json`
- [ ] Create `.prettierrc.json`
- [ ] Run: `npm run lint -- --fix`

### Lazy Loading
- [ ] `/ui/src/App.tsx`:
  ```typescript
  const ChatInterface = lazy(() => import('./components/ChatInterface'))
  const MetricsView = lazy(() => import('./components/MetricsView'))
  
  {viewMode === 'chat' && <Suspense fallback={<LoadingSpinner />}><ChatInterface /></Suspense>}
  ```

### Color Contrast Testing
- [ ] Use WebAIM Contrast Checker tool
- [ ] Test neon-green (#B8FF00) against neon-surface (#0F0F1E)
- [ ] Test neon-text colors
- [ ] Update colors if contrast < 4.5:1

### Final Testing Checklist
- [ ] TypeScript compilation with no errors: `npm run build`
- [ ] No console errors: Open dev tools console
- [ ] Error boundaries work: Manually throw error in component
- [ ] Network errors show retry: Disconnect network, test components
- [ ] Keyboard navigation: Tab through all interactive elements
- [ ] Screen reader: Test with NVDA or JAWS
- [ ] Performance: Run Lighthouse audit
- [ ] Memory leaks: React DevTools Profiler
- [ ] Type checking: `tsc --noEmit`

---

## Summary Metrics

After completing all phases:
- [ ] 0 TypeScript `any` types
- [ ] 0 unhandled promise rejections
- [ ] 0 console warnings/errors in production
- [ ] 100% components have ARIA labels
- [ ] 100% forms have labels
- [ ] Color contrast >= 4.5:1
- [ ] All async operations have cleanup
- [ ] All API calls have error handling
- [ ] Keyboard navigation fully functional
- [ ] No memory leaks

**Total Estimated Effort: 56 hours (2 weeks)**
**Recommended Daily: 5.6 hours/day for 10 days**

