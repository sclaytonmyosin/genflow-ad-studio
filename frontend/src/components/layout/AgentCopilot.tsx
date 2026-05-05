import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Fab,
  Paper,
  TextField,
  InputAdornment,
  CircularProgress,
} from '@mui/material';
import {
  AutoAwesome,
  Close,
  Send,
} from '@mui/icons-material';
import { apiUrl } from '../../lib/url';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  steps?: string[];
}

export default function AgentCopilot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'agent',
      content: "Hello! I'm the Myosin Brain — powered by Gemini 3 Pro. I can create campaigns, generate videos, and check your pipeline. What can I do for you?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    if (open) scrollToBottom();
  }, [messages, open]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiUrl('/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!res.ok) throw new Error('Failed to get response');
      const data = await res.json();

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: data.response || 'Done.',
        steps: data.steps || [],
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: 'Sorry, I encountered an error. Please check the backend logs.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating trigger */}
      <Fab
        onClick={() => setOpen((prev) => !prev)}
        sx={{
          position: 'fixed',
          right: 16,
          bottom: 96,
          zIndex: 1300,
          width: 52,
          height: 52,
          background: open
            ? 'linear-gradient(135deg, #dc2626, #ef4444)'
            : 'linear-gradient(135deg, #0066FF, #06b6d4)',
          boxShadow: open
            ? '0 4px 20px rgba(239, 68, 68, 0.45)'
            : '0 4px 20px rgba(0, 102, 255, 0.45)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            background: open
              ? 'linear-gradient(135deg, #b91c1c, #dc2626)'
              : 'linear-gradient(135deg, #1A75FF, #22d3ee)',
            transform: 'scale(1.05)',
          },
        }}
      >
        <AutoAwesome sx={{ color: '#fff', fontSize: 22 }} />
      </Fab>

      {/* Chat panel */}
      {open && (
        <Paper
          elevation={0}
          sx={{
            position: 'fixed',
            right: 16,
            bottom: 164,
            width: 390,
            height: 560,
            maxHeight: '72vh',
            zIndex: 1300,
            display: 'flex',
            flexDirection: 'column',
            borderRadius: '16px',
            overflow: 'hidden',
            backgroundColor: 'rgba(11, 14, 17, 0.96)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            border: '1px solid rgba(6, 182, 212, 0.25)',
            boxShadow: '0 24px 64px rgba(0,0,0,0.55), 0 0 0 1px rgba(6, 182, 212, 0.10)',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              p: 2,
              background: 'linear-gradient(135deg, rgba(0, 102, 255, 0.30) 0%, rgba(6, 182, 212, 0.20) 100%)',
              borderBottom: '1px solid rgba(6, 182, 212, 0.20)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #0066FF, #06b6d4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid rgba(34, 211, 238, 0.55)',
                  boxShadow: '0 0 12px rgba(6, 182, 212, 0.55)',
                }}
              >
                <AutoAwesome sx={{ fontSize: 16, color: '#fff' }} />
              </Box>
              <Box>
                <Typography
                  sx={{
                    fontFamily: '"Inter", system-ui, sans-serif',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                    color: '#E8EEF5',
                    lineHeight: 1,
                    letterSpacing: '-0.01em',
                  }}
                >
                  myosin brain
                </Typography>
                <Typography
                  sx={{
                    fontFamily: '"IBM Plex Mono", monospace',
                    fontSize: '0.6rem',
                    letterSpacing: '0.20em',
                    textTransform: 'uppercase',
                    color: '#22d3ee',
                    lineHeight: 1,
                    mt: 0.4,
                    fontWeight: 500,
                  }}
                >
                  gemini 3 pro
                </Typography>
              </Box>
            </Box>
            <IconButton
              size="small"
              onClick={() => setOpen(false)}
              sx={{ color: 'rgba(232,238,245,0.6)', '&:hover': { color: '#E8EEF5' } }}
            >
              <Close fontSize="small" />
            </IconButton>
          </Box>

          {/* Messages */}
          <Box
            sx={{
              flex: 1,
              overflowY: 'auto',
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
              '&::-webkit-scrollbar': { width: 4 },
              '&::-webkit-scrollbar-thumb': { background: 'rgba(6, 182, 212, 0.30)', borderRadius: 4 },
            }}
          >
            {messages.map((msg) => (
              <Box
                key={msg.id}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <Box
                  sx={{
                    maxWidth: '85%',
                    p: '10px 14px',
                    borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                    background: msg.role === 'user'
                      ? 'linear-gradient(135deg, #0066FF, #06b6d4)'
                      : 'rgba(6, 182, 212, 0.06)',
                    border: msg.role === 'agent' ? '1px solid rgba(6, 182, 212, 0.18)' : 'none',
                    boxShadow: msg.role === 'user' ? '0 2px 12px rgba(0, 102, 255, 0.30)' : 'none',
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: msg.role === 'user' ? '#fff' : '#D9E2EC',
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.6,
                      fontSize: '0.875rem',
                    }}
                  >
                    {msg.content}
                  </Typography>
                </Box>
                {msg.steps && msg.steps.length > 0 && (
                  <Box sx={{ mt: 0.5, pl: 0.5 }}>
                    {msg.steps.map((step, idx) => (
                      <Typography
                        key={idx}
                        variant="caption"
                        sx={{
                          color: '#22d3ee',
                          display: 'block',
                          fontSize: '0.7rem',
                          letterSpacing: '0.02em',
                          fontFamily: '"IBM Plex Mono", monospace',
                        }}
                      >
                        ✦ {step}
                      </Typography>
                    ))}
                  </Box>
                )}
              </Box>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', pl: 0.5 }}>
                <CircularProgress size={14} thickness={5} sx={{ color: '#22d3ee' }} />
                <Typography
                  variant="caption"
                  sx={{ color: '#22d3ee', fontSize: '0.75rem', fontFamily: '"IBM Plex Mono", monospace' }}
                >
                  thinking…
                </Typography>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

          {/* Input */}
          <Box
            sx={{
              p: 1.5,
              borderTop: '1px solid rgba(6, 182, 212, 0.15)',
            }}
          >
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Ask Myosin Brain…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              multiline
              maxRows={3}
              InputProps={{
                sx: {
                  borderRadius: '12px',
                  fontSize: '0.875rem',
                  backgroundColor: 'rgba(2, 6, 23, 0.50)',
                  color: '#E8EEF5',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(6, 182, 212, 0.25)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(6, 182, 212, 0.50)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#22d3ee',
                  },
                },
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleSend}
                      disabled={!input.trim() || loading}
                      sx={{
                        background: input.trim() ? 'linear-gradient(135deg, #0066FF, #06b6d4)' : 'transparent',
                        color: input.trim() ? '#fff' : 'rgba(6, 182, 212, 0.45)',
                        width: 32,
                        height: 32,
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #1A75FF, #22d3ee)',
                          transform: 'scale(1.05)',
                        },
                        '&.Mui-disabled': { background: 'transparent' },
                      }}
                    >
                      <Send sx={{ fontSize: 16 }} />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Paper>
      )}
    </>
  );
}
