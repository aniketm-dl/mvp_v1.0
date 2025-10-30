import React, { useState, useEffect, useRef } from 'react'
import { Send, Zap, Loader2 } from 'lucide-react'
import { useStore } from '../store/useStore'
import { chatAPI } from '../api/client'
import { ChatSidebar } from './ChatSidebar'
import { ChatMessage } from './ChatMessage'
import { ChatTwinProfile } from './ChatTwinProfile'
import { ChatExperimentPanel } from './ChatExperimentPanel'
import type { Conversation, ChatMessage as ChatMessageType } from '../types'
import { getTwinName } from '../utils/twinNames'

export const ChatInterface: React.FC = () => {
  const {
    twins,
    activeChatTwinId,
    activeConversationId,
    conversations,
    chatLoading,
    setActiveConversation,
    addConversation,
    updateConversation,
    setChatLoading,
  } = useStore()

  const [inputMessage, setInputMessage] = useState('')
  const [currentMessages, setCurrentMessages] = useState<ChatMessageType[]>([])
  const [showExperimentPanel, setShowExperimentPanel] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Find active twin
  const activeTwin = twins.find((t) => t.id === activeChatTwinId) || null
  const twinName = activeTwin ? getTwinName(activeTwin.id) : ''

  // Load conversation messages when conversation changes
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

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentMessages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !activeChatTwinId || chatLoading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setChatLoading(true)

    try {
      const response = await chatAPI.sendMessage(
        activeChatTwinId,
        userMessage,
        activeConversationId || undefined
      )

      // Update messages
      setCurrentMessages((prev) => [
        ...prev,
        response.user_message,
        response.twin_response,
      ])

      // If new conversation, update state
      if (!activeConversationId) {
        setActiveConversation(response.conversation_id)

        // Create conversation object
        const newConversation: Conversation = {
          id: response.conversation_id,
          twin_id: activeChatTwinId,
          messages: [response.user_message, response.twin_response],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          preview: userMessage,
          message_count: 2,
        }
        addConversation(newConversation)
      } else {
        // Update existing conversation
        const existingConv = conversations.find((c) => c.id === activeConversationId)
        if (existingConv) {
          const updatedConv: Conversation = {
            ...existingConv,
            messages: [
              ...existingConv.messages,
              response.user_message,
              response.twin_response,
            ],
            updated_at: new Date().toISOString(),
            message_count: (existingConv.message_count || 0) + 2,
          }
          updateConversation(updatedConv)
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      alert('Failed to send message. Please try again.')
    } finally {
      setChatLoading(false)
    }
  }

  const handleRunExperiment = async (experimentConfig: any) => {
    if (!activeChatTwinId || !activeConversationId || chatLoading) {
      alert('Please start a conversation first')
      return
    }

    setShowExperimentPanel(false)
    setChatLoading(true)

    try {
      const result = await chatAPI.runExperiment(
        activeChatTwinId,
        activeConversationId,
        experimentConfig
      )

      // Add experiment result as a special message
      const experimentMessage: ChatMessageType = {
        id: `exp_${Date.now()}`,
        role: 'assistant',
        content: 'Experiment completed',
        timestamp: new Date().toISOString(),
        metadata: {
          isExperiment: true,
          experimentResult: result.decision,
        },
      }

      setCurrentMessages((prev) => [...prev, experimentMessage])

      // Update conversation
      const existingConv = conversations.find((c) => c.id === activeConversationId)
      if (existingConv) {
        const updatedConv: Conversation = {
          ...existingConv,
          messages: [...existingConv.messages, experimentMessage],
          updated_at: new Date().toISOString(),
          message_count: (existingConv.message_count || 0) + 1,
        }
        updateConversation(updatedConv)
      }
    } catch (error) {
      console.error('Failed to run experiment:', error)
      alert('Failed to run experiment. Please try again.')
    } finally {
      setChatLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="h-[calc(100vh-200px)] grid grid-cols-12 gap-6">
      {/* Left Sidebar - Twin Selector & Conversation History (25%) */}
      <div className="col-span-3 card overflow-hidden flex flex-col">
        <ChatSidebar twins={twins} />
      </div>

      {/* Center Panel - Chat Messages (50%) */}
      <div className="col-span-6 card flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-neon-surfacelight flex items-center justify-between">
          <div>
            {activeTwin ? (
              <>
                <h3 className="font-bold text-lg">Chat with {twinName}</h3>
                <p className="text-xs text-neon-textsecondary">
                  {activeConversationId
                    ? 'Continue your conversation'
                    : 'Start a new conversation'}
                </p>
              </>
            ) : (
              <>
                <h3 className="font-bold text-lg">Chat with Twins</h3>
                <p className="text-xs text-neon-textsecondary">
                  Select a twin from the sidebar to start chatting
                </p>
              </>
            )}
          </div>
          {activeTwin && activeConversationId && (
            <button
              onClick={() => setShowExperimentPanel(true)}
              className="flex items-center gap-2 px-3 py-2 bg-neon-green/10 text-neon-green border border-neon-green/30 rounded-lg hover:bg-neon-green/20 transition-all text-sm font-medium"
              disabled={chatLoading}
            >
              <Zap className="w-4 h-4" />
              Test Offer
            </button>
          )}
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4">
          {currentMessages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-center text-neon-textsecondary">
              <div>
                {activeTwin ? (
                  <>
                    <p className="mb-2">Start a conversation with {twinName}</p>
                    <p className="text-xs">
                      Ask about preferences, travel habits, or test offers
                    </p>
                  </>
                ) : (
                  <>
                    <p className="mb-2">No conversation selected</p>
                    <p className="text-xs">
                      Select a twin from the sidebar to begin
                    </p>
                  </>
                )}
              </div>
            </div>
          ) : (
            <>
              {currentMessages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  twinId={activeChatTwinId || undefined}
                  isExperiment={msg.metadata?.isExperiment}
                  experimentResult={msg.metadata?.experimentResult}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-neon-surfacelight">
          {activeTwin ? (
            <div className="flex gap-3">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={`Message ${twinName}...`}
                className="input flex-1 resize-none"
                rows={2}
                disabled={chatLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || chatLoading}
                className="btn-primary px-4 h-auto disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {chatLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          ) : (
            <div className="text-center text-neon-textsecondary text-sm">
              Select a twin to start chatting
            </div>
          )}
        </div>
      </div>

      {/* Right Sidebar - Twin Profile (25%) */}
      <div className="col-span-3 overflow-y-auto">
        <ChatTwinProfile twin={activeTwin} />
      </div>

      {/* Experiment Panel Modal */}
      <ChatExperimentPanel
        isOpen={showExperimentPanel}
        onClose={() => setShowExperimentPanel(false)}
        onRunExperiment={handleRunExperiment}
      />
    </div>
  )
}
