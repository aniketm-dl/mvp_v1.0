import React, { useEffect } from 'react'
import { Plus, MessageSquare, Trash2, Clock } from 'lucide-react'
import type { AirlineTwin, Conversation } from '../types'
import { useStore } from '../store/useStore'
import { getTwinName } from '../utils/twinNames'
import { chatAPI } from '../api/client'

interface ChatSidebarProps {
  twins: AirlineTwin[]
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({ twins }) => {
  const {
    activeChatTwinId,
    activeConversationId,
    conversations,
    setActiveChatTwin,
    setActiveConversation,
    setConversations,
    removeConversation,
    startNewChat,
  } = useStore()

  // Load conversations on mount
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const data = await chatAPI.getHistory()
        setConversations(data.conversations)
      } catch (error) {
        console.error('Failed to load conversations:', error)
      }
    }
    loadConversations()
  }, [setConversations])

  const handleTwinSelect = (twinId: string) => {
    startNewChat(twinId)
  }

  const handleConversationSelect = async (conversation: Conversation) => {
    setActiveChatTwin(conversation.twin_id)
    setActiveConversation(conversation.id)
  }

  const handleDeleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Delete this conversation?')) {
      try {
        await chatAPI.deleteConversation(conversationId)
        removeConversation(conversationId)
        if (activeConversationId === conversationId) {
          setActiveConversation(null)
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error)
      }
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  // Group conversations by twin
  const conversationsByTwin = conversations.reduce((acc, conv) => {
    if (!acc[conv.twin_id]) acc[conv.twin_id] = []
    acc[conv.twin_id].push(conv)
    return acc
  }, {} as Record<string, Conversation[]>)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-neon-surfacelight">
        <h3 className="font-bold text-lg mb-1">Chat with Twins</h3>
        <p className="text-xs text-neon-textsecondary">
          Select a twin or conversation to start
        </p>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Twin Selector */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-neon-textsecondary">Twins</h4>
          </div>
          <div className="space-y-1">
            {twins.map((twin) => {
              const twinName = getTwinName(twin.id)
              const isActive = activeChatTwinId === twin.id && !activeConversationId
              const twinConversations = conversationsByTwin[twin.id] || []

              return (
                <div key={twin.id} className="space-y-1">
                  {/* Twin Button */}
                  <button
                    onClick={() => handleTwinSelect(twin.id)}
                    className={`w-full flex items-center gap-3 p-2 rounded-lg transition-all text-left ${
                      isActive
                        ? 'bg-neon-green/20 border border-neon-green/50'
                        : 'hover:bg-neon-surfacelight border border-transparent'
                    }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                        isActive
                          ? 'bg-neon-green/30 text-neon-green'
                          : 'bg-neon-blue/20 text-neon-blue'
                      }`}
                    >
                      {twinName.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{twinName}</div>
                      <div className="text-xs text-neon-textsecondary">
                        {twinConversations.length} conversation{twinConversations.length !== 1 ? 's' : ''}
                      </div>
                    </div>
                    <Plus className="w-4 h-4 text-neon-green flex-shrink-0" />
                  </button>

                  {/* Conversations for this twin */}
                  {twinConversations.length > 0 && (
                    <div className="ml-4 space-y-1">
                      {twinConversations.map((conv) => (
                        <button
                          key={conv.id}
                          onClick={() => handleConversationSelect(conv)}
                          className={`w-full flex items-start gap-2 p-2 rounded-lg transition-all text-left group ${
                            activeConversationId === conv.id
                              ? 'bg-neon-blue/20 border border-neon-blue/50'
                              : 'hover:bg-neon-surfacelight border border-transparent'
                          }`}
                        >
                          <MessageSquare className="w-3 h-3 mt-0.5 text-neon-textsecondary flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="text-xs truncate">{conv.preview || 'New conversation'}</div>
                            <div className="flex items-center gap-1 mt-1">
                              <Clock className="w-3 h-3 text-neon-textsecondary" />
                              <span className="text-xs text-neon-textsecondary">
                                {formatDate(conv.updated_at)}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={(e) => handleDeleteConversation(conv.id, e)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Trash2 className="w-3 h-3 text-red-400 hover:text-red-300" />
                          </button>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
