'use client';

/**
 * ConversationList — FR-23
 *
 * Sidebar component listing all messaging conversations.
 * Shows participant info, last message preview, and unread badge.
 */

import clsx from 'clsx';

interface Conversation {
  id: string;
  participant_a_id: string;
  participant_b_id: string;
  service_request_id: string | null;
  last_message_at: string | null;
  status: string;
  created_at: string;
}

interface ConversationListProps {
  conversations: Conversation[];
  selectedId: string | null;
  currentUserId: string;
  onSelect: (id: string) => void;
}

export default function ConversationList({
  conversations,
  selectedId,
  currentUserId,
  onSelect,
}: ConversationListProps) {
  const getOtherParticipantId = (conv: Conversation) =>
    conv.participant_a_id === currentUserId
      ? conv.participant_b_id
      : conv.participant_a_id;

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return d.toLocaleDateString([], { weekday: 'short' });
    }
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  if (conversations.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-3 bg-cultivax-elevated rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-cultivax-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
          </div>
          <p className="text-sm text-cultivax-text-muted">No conversations yet</p>
          <p className="text-xs text-cultivax-text-muted mt-1">
            Start a conversation from a service request
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {conversations.map((conv) => {
        const otherId = getOtherParticipantId(conv);
        const isSelected = conv.id === selectedId;

        return (
          <button
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            className={clsx(
              'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
              'border-b border-cultivax-border/50',
              isSelected
                ? 'bg-cultivax-primary/10 border-l-2 border-l-cultivax-primary'
                : 'hover:bg-cultivax-elevated'
            )}
          >
            {/* Avatar */}
            <div className="w-10 h-10 rounded-full bg-cultivax-primary/15 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-cultivax-primary">
                {otherId.charAt(0).toUpperCase()}
              </span>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-cultivax-text-primary truncate">
                  User {otherId.slice(0, 8)}…
                </span>
                <span className="text-[10px] text-cultivax-text-muted flex-shrink-0 ml-2">
                  {formatTime(conv.last_message_at)}
                </span>
              </div>
              <div className="flex items-center gap-1 mt-0.5">
                {conv.service_request_id && (
                  <span className="text-[9px] bg-cultivax-primary/10 text-cultivax-primary px-1.5 py-0.5 rounded-full font-medium">
                    Service
                  </span>
                )}
                <span className="text-xs text-cultivax-text-muted truncate">
                  {conv.status === 'archived' ? 'Archived' : 'Tap to view'}
                </span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
