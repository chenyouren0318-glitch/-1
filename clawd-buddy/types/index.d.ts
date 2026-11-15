declare module 'claude-code' {
  interface PluginState {
    'clawd-buddy': {
      turnStartedAt: number | null
      lastActiveAt: number | null
      isHidden: boolean
    }
  }
}
export type ClawdMood = 'idle' | 'typing' | 'tired'
