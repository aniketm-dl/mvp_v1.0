import React from 'react'
import { User, Bot, CheckCircle, XCircle } from 'lucide-react'
import type { ChatMessage as ChatMessageType, TwinDecision } from '../types'
import { getTwinName } from '../utils/twinNames'

interface ChatMessageProps {
  message: ChatMessageType
  twinId?: string
  isExperiment?: boolean
  experimentResult?: TwinDecision
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  twinId,
  isExperiment,
  experimentResult,
}) => {
  const isUser = message.role === 'user'
  const timestamp = new Date(message.timestamp).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  })

  if (isExperiment && experimentResult) {
    return (
      <div className="mb-4 flex justify-end">
        <div className="max-w-[80%]">
          <div className="card bg-neon-surfacelight border-neon-blue/30 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-neon-blue/20 flex items-center justify-center">
                {experimentResult.response.decision === 'yes' ? (
                  <CheckCircle className="w-4 h-4 text-neon-green" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
              </div>
              <div>
                <div className="font-semibold text-sm">
                  Experiment Result
                </div>
                <div className="text-xs text-neon-textsecondary">{timestamp}</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neon-textsecondary">Decision:</span>
                <span
                  className={`font-bold uppercase ${
                    experimentResult.response.decision === 'yes'
                      ? 'text-neon-green'
                      : 'text-red-400'
                  }`}
                >
                  {experimentResult.response.decision}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-neon-textsecondary">Probability:</span>
                <span className="font-semibold text-neon-blue">
                  {(experimentResult.response.probability * 100).toFixed(0)}%
                </span>
              </div>

              <div className="mt-3 pt-3 border-t border-neon-surfacelight">
                <div className="text-xs text-neon-textsecondary mb-1">Rationale:</div>
                <div className="text-sm italic">{experimentResult.response.rationale}</div>
              </div>

              <div className="mt-3 pt-3 border-t border-neon-surfacelight">
                <div className="text-xs text-neon-textsecondary mb-2">Offer Details:</div>
                <div className="text-xs space-y-1">
                  <div>
                    <span className="text-neon-textsecondary">Type: </span>
                    {experimentResult.task.offer.offer_kind}
                  </div>
                  <div>
                    <span className="text-neon-textsecondary">Discount: </span>
                    {(experimentResult.task.offer.discount_pct * 100).toFixed(0)}%
                  </div>
                  <div>
                    <span className="text-neon-textsecondary">Context: </span>
                    {experimentResult.task.context.flight_length} flight,{' '}
                    {experimentResult.task.context.trip_purpose}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`mb-4 flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
            isUser
              ? 'bg-neon-green/20 text-neon-green'
              : 'bg-neon-blue/20 text-neon-blue'
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4" />
          ) : twinId ? (
            getTwinName(twinId).charAt(0)
          ) : (
            <Bot className="w-4 h-4" />
          )}
        </div>

        {/* Message bubble */}
        <div
          className={`rounded-lg p-3 ${
            isUser
              ? 'bg-neon-green/10 border border-neon-green/30'
              : 'bg-neon-surfacelight border border-neon-blue/20'
          }`}
        >
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
          <div
            className={`text-xs mt-1 ${
              isUser ? 'text-neon-green/60' : 'text-neon-textsecondary'
            }`}
          >
            {timestamp}
          </div>
        </div>
      </div>
    </div>
  )
}
