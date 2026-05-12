import { useState, useEffect, useCallback } from 'react'

const API = 'http://localhost:8000'
const mono = { fontFamily: "'Share Tech Mono', monospace" }
const raj  = { fontFamily: "'Rajdhani', sans-serif" }

// ── Primitive controls ────────────────────────────────────────────────────────

function Toggle({ value, onChange }) {
  return (
    <div
      onClick={() => onChange(!value)}
      title={value ? 'Click to disable' : 'Click to enable'}
      style={{
        width: 42, height: 22, borderRadius: 11, flexShrink: 0,
        background:    value ? 'rgba(80,180,255,0.25)' : 'rgba(60,80,100,0.2)',
        border:        `1px solid ${value ? 'rgba(80,180,255,0.55)' : 'rgba(80,100,120,0.3)'}`,
        boxShadow:     value ? '0 0 8px rgba(80,180,255,0.2)' : 'none',
        cursor:        'pointer',
        position:      'relative',
        transition:    'all 0.22s ease',
      }}>
      <div style={{
        position:   'absolute',
        top: 3, left: value ? 22 : 3,
        width: 14, height: 14, borderRadius: '50%',
        background:  value ? '#4fc3f7' : 'rgba(120,140,160,0.55)',
        boxShadow:   value ? '0 0 7px rgba(80,180,255,0.9)' : 'none',
        transition:  'left 0.22s ease, background 0.22s ease',
      }} />
    </div>
  )
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        ...mono, fontSize: 11,
        background:  'rgba(255,255,255,0.04)',
        border:      '1px solid rgba(80,180,255,0.2)',
        borderRadius: 5,
        padding:     '5px 10px',
        color:       '#c8e6ff',
        outline:     'none',
        cursor:      'pointer',
        minWidth:    140,
      }}>
      {options.map(o => (
        <option key={o.value} value={o.value} style={{ background: '#0d1525' }}>
          {o.label}
        </option>
      ))}
    </select>
  )
}

function TextInput({ value, onChange, placeholder, width = '100%' }) {
  return (
    <input
      value={value ?? ''}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        ...mono, fontSize: 11,
        width,
        background:  'rgba(255,255,255,0.04)',
        border:      '1px solid rgba(80,180,255,0.2)',
        borderRadius: 5,
        padding:     '6px 10px',
        color:       '#c8e6ff',
        outline:     'none',
        boxSizing:   'border-box',
      }}
    />
  )
}

function NumberInput({ value, onChange, min, max, step = 1, width = 70 }) {
  return (
    <input
      type="number" min={min} max={max} step={step}
      value={value ?? ''}
      onChange={e => onChange(Number(e.target.value))}
      style={{
        ...mono, fontSize: 11,
        width,
        background:  'rgba(255,255,255,0.04)',
        border:      '1px solid rgba(80,180,255,0.2)',
        borderRadius: 5,
        padding:     '5px 8px',
        color:       '#c8e6ff',
        outline:     'none',
        textAlign:   'center',
      }}
    />
  )
}

// ── Layout primitives ─────────────────────────────────────────────────────────

function SectionHeader({ title, children, action }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'space-between',
        marginBottom:   12,
        paddingBottom:  6,
        borderBottom:   '1px solid rgba(80,180,255,0.12)',
      }}>
        <span style={{ ...raj, fontSize: 10, letterSpacing: 4, color: 'rgba(80,180,255,0.5)' }}>
          {title}
        </span>
        {action}
      </div>
      {children}
    </div>
  )
}

function SettingRow({ label, hint, children, restart }) {
  return (
    <div style={{
      display:        'flex',
      alignItems:     'center',
      justifyContent: 'space-between',
      padding:        '9px 0',
      borderBottom:   '1px solid rgba(80,180,255,0.05)',
      gap:            12,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ ...mono, fontSize: 10, color: 'rgba(180,210,240,0.75)', letterSpacing: 0.8 }}>
          {label}
          {restart && (
            <span style={{ marginLeft: 8, color: 'rgba(253,186,116,0.6)', fontSize: 9 }}>
              ↺ restart
            </span>
          )}
        </div>
        {hint && (
          <div style={{ ...raj, fontSize: 10, color: 'rgba(80,130,180,0.4)', marginTop: 2 }}>
            {hint}
          </div>
        )}
      </div>
      <div style={{ flexShrink: 0 }}>{children}</div>
    </div>
  )
}

// ── Status row ────────────────────────────────────────────────────────────────

function StatusRow({ label, ok, text, children }) {
  const dot = ok === null ? '#fbbf24' : ok ? '#4ade80' : '#f87171'
  return (
    <div style={{
      padding:      '8px 0',
      borderBottom: '1px solid rgba(80,180,255,0.05)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <div style={{
          width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
          background: dot, boxShadow: `0 0 6px ${dot}`,
        }} />
        <span style={{ ...mono, fontSize: 10, color: 'rgba(180,210,240,0.75)', flex: 1, letterSpacing: 0.5 }}>
          {label}
        </span>
        <span style={{ ...mono, fontSize: 9, color: dot, letterSpacing: 0.5 }}>
          {text}
        </span>
      </div>
      {children && (
        <div style={{ marginLeft: 16, marginTop: 4 }}>
          {children}
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

const WHISPER_MODELS = [
  { value: 'tiny',   label: 'tiny   — fastest, least accurate' },
  { value: 'base',   label: 'base   — good balance (default)'  },
  { value: 'small',  label: 'small  — more accurate, slower'   },
  { value: 'medium', label: 'medium — most accurate, slowest'  },
]

const TTS_VOICES = [
  { value: 'en-US-GuyNeural',    label: 'Guy (US, Male)'       },
  { value: 'en-US-AriaNeural',   label: 'Aria (US, Female)'    },
  { value: 'en-GB-RyanNeural',   label: 'Ryan (UK, Male)'      },
  { value: 'en-GB-SoniaNeural',  label: 'Sonia (UK, Female)'   },
  { value: 'en-AU-WilliamNeural',label: 'William (AU, Male)'   },
]

export default function SettingsPanel() {
  const [status,    setStatus]    = useState(null)
  const [cfg,       setCfg]       = useState(null)
  const [saveState, setSaveState] = useState('idle')  // idle | saving | saved | error
  const [lastPoll,  setLastPoll]  = useState(null)

  const loadStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/status`)
      if (r.ok) {
        setStatus(await r.json())
        setLastPoll(new Date().toLocaleTimeString())
      }
    } catch { /* backend offline */ }
  }, [])

  const loadSettings = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/settings`)
      if (r.ok) setCfg(await r.json())
    } catch { /* backend offline */ }
  }, [])

  useEffect(() => {
    loadStatus()
    loadSettings()
    const t = setInterval(loadStatus, 30_000)
    return () => clearInterval(t)
  }, [loadStatus, loadSettings])

  const set = key => val => setCfg(c => ({ ...c, [key]: val }))

  async function handleSave() {
    if (!cfg) return
    setSaveState('saving')
    try {
      const r = await fetch(`${API}/api/settings`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(cfg),
      })
      setSaveState(r.ok ? 'saved' : 'error')
    } catch {
      setSaveState('error')
    }
    setTimeout(() => setSaveState('idle'), 3500)
  }

  const s = status    // shorthand
  const c = cfg || {} // safe shorthand

  return (
    <div style={{
      height:          '100%',
      overflowY:       'auto',
      padding:         '28px 36px 100px',
      scrollbarWidth:  'thin',
      scrollbarColor:  'rgba(80,160,255,0.15) transparent',
    }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 28 }}>
        <div style={{ ...mono, fontSize: 14, letterSpacing: 5, color: '#c8e6ff' }}>
          ⚙ SETTINGS
        </div>
        <div style={{ ...raj, fontSize: 10, color: 'rgba(80,130,180,0.4)', letterSpacing: 2 }}>
          JARVIS v4.0
        </div>
      </div>

      {/* ── 1. SYSTEM STATUS ───────────────────────────────────────────────── */}
      <SectionHeader
        title="SYSTEM STATUS"
        action={
          <button onClick={loadStatus} style={{
            ...raj, fontSize: 9, letterSpacing: 2,
            background: 'transparent',
            border:     '1px solid rgba(80,180,255,0.2)',
            borderRadius: 4,
            color:      'rgba(80,180,255,0.5)',
            padding:    '2px 8px',
            cursor:     'pointer',
          }}>
            ↺ REFRESH{lastPoll ? `  ${lastPoll}` : ''}
          </button>
        }
      >
        {!s ? (
          <div style={{ ...mono, fontSize: 10, color: 'rgba(80,130,180,0.4)', padding: '8px 0' }}>
            Loading…
          </div>
        ) : (
          <>
            <StatusRow
              label="CLAUDE API"
              ok={s.claude?.ok}
              text={s.claude?.ok ? `ONLINE  ·  ${s.claude.model}` : 'OFFLINE'}
            />
            <StatusRow
              label="TELEGRAM BOT"
              ok={s.telegram?.ok}
              text={
                !s.telegram?.configured ? 'NOT CONFIGURED' :
                s.telegram?.ok          ? `CONNECTED` :
                s.telegram?.running     ? 'STARTING' : 'OFFLINE'
              }
            >
              {s.telegram?.ok && s.telegram?.chat_id && (
                <div style={{ ...mono, fontSize: 9, color: 'rgba(80,180,255,0.4)' }}>
                  chat_id: {s.telegram.chat_id}
                </div>
              )}
              {!s.telegram?.configured && (
                <div style={{ ...raj, fontSize: 10, color: 'rgba(253,186,116,0.5)' }}>
                  Set TELEGRAM_BOT_TOKEN in .env
                </div>
              )}
            </StatusRow>
            <StatusRow
              label="MCP SERVERS"
              ok={s.mcp?.ok && s.mcp?.servers?.length > 0 ? true : s.mcp?.ok ? null : false}
              text={
                !s.mcp?.ok                  ? 'OFFLINE' :
                s.mcp.servers.length === 0   ? 'NO SERVERS' :
                `${s.mcp.servers.length} CONNECTED  ·  ${s.mcp.tool_count} TOOLS`
              }
            >
              {s.mcp?.servers?.map(sv => (
                <div key={sv.name} style={{ ...mono, fontSize: 9, color: 'rgba(80,180,255,0.4)', marginTop: 2 }}>
                  └ {sv.name}  ({sv.tool_count} tools)
                </div>
              ))}
            </StatusRow>
            <StatusRow
              label="WAKE WORD"
              ok={s.wakeword?.running ? true : null}
              text={s.wakeword?.running ? 'LISTENING' : 'STOPPED'}
            />
            <StatusRow
              label="OBSIDIAN VAULT"
              ok={s.obsidian?.ok}
              text={
                !s.obsidian?.configured ? 'NOT CONFIGURED' :
                s.obsidian?.ok          ? 'SYNCED' : 'ERROR'
              }
            >
              {s.obsidian?.summary && s.obsidian.configured && (
                <div style={{ ...mono, fontSize: 9, color: 'rgba(80,180,255,0.4)' }}>
                  {s.obsidian.summary}
                </div>
              )}
            </StatusRow>
            <StatusRow
              label="SCHEDULER"
              ok={s.scheduler?.running ? true : null}
              text={s.scheduler?.running ? 'ACTIVE' : 'STOPPED'}
            />
            <StatusRow
              label="MEMORY"
              ok={s.memory?.ok}
              text={
                s.memory?.ok
                  ? `${s.memory.facts} FACTS  ·  ${s.memory.messages} MESSAGES`
                  : 'ERROR'
              }
            />
            <StatusRow
              label="WHISPER STT"
              ok={s.whisper?.ok ? true : null}
              text={
                !s.whisper?.ok      ? 'UNAVAILABLE' :
                s.whisper?.loaded   ? `LOADED  ·  ${s.whisper.model}` :
                                      `STANDBY  ·  ${s.whisper.model}`
              }
            />
          </>
        )}
      </SectionHeader>

      {/* ── 2. VOICE & AUDIO ───────────────────────────────────────────────── */}
      <SectionHeader title="VOICE & AUDIO">
        <SettingRow label="WHISPER MODEL" restart hint="larger = more accurate but slower on first load">
          <Select
            value={c.whisper_model || 'base'}
            onChange={set('whisper_model')}
            options={WHISPER_MODELS}
          />
        </SettingRow>
        <SettingRow label="WAKE WORD LISTENER" restart hint="'Hey JARVIS' hotword via microphone">
          <Toggle value={c.wakeword_enabled ?? true} onChange={set('wakeword_enabled')} />
        </SettingRow>
        <SettingRow label="WAKE WORD THRESHOLD" hint={`${((c.wakeword_threshold || 0.5) * 100).toFixed(0)}% confidence required`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="range" min="0.2" max="0.95" step="0.05"
              value={c.wakeword_threshold || 0.5}
              onChange={e => set('wakeword_threshold')(parseFloat(e.target.value))}
              style={{ width: 100, accentColor: '#4fc3f7', cursor: 'pointer' }}
            />
            <span style={{ ...mono, fontSize: 10, color: 'rgba(80,180,255,0.6)', width: 32 }}>
              {(c.wakeword_threshold || 0.5).toFixed(2)}
            </span>
          </div>
        </SettingRow>
        <SettingRow label="TTS VOICE" hint="Microsoft neural voice (edge-tts)">
          <Select
            value={c.tts_voice || 'en-US-GuyNeural'}
            onChange={set('tts_voice')}
            options={TTS_VOICES}
          />
        </SettingRow>
        <SettingRow label="BROWSER HEADLESS" restart hint="show/hide Playwright browser window">
          <Toggle value={c.browser_headless ?? true} onChange={set('browser_headless')} />
        </SettingRow>
      </SectionHeader>

      {/* ── 3. ALERTS & SCHEDULING ─────────────────────────────────────────── */}
      <SectionHeader title="ALERTS & SCHEDULING">
        <SettingRow label="MORNING BRIEFING HOUR" hint="24h format — 0 to 23">
          <NumberInput
            value={c.briefing_hour ?? 8}
            onChange={set('briefing_hour')}
            min={0} max={23}
          />
        </SettingRow>
        <SettingRow label="STOCK ALERT TICKERS" hint="comma-separated, checked every 5 minutes">
          <TextInput
            value={c.alert_tickers || ''}
            onChange={set('alert_tickers')}
            placeholder="AAPL,NVDA,BTC-USD"
            width={200}
          />
        </SettingRow>
        <SettingRow label="PRICE ALERT THRESHOLD %" hint="trigger alert when move ≥ this percent">
          <NumberInput
            value={c.price_alert_pct ?? 2.5}
            onChange={set('price_alert_pct')}
            min={0.5} max={20} step={0.5}
            width={70}
          />
        </SettingRow>
        <SettingRow label="HOURLY EMAIL DIGEST" hint="opt-in — triages inbox every hour">
          <Toggle value={c.email_digest_enabled ?? false} onChange={set('email_digest_enabled')} />
        </SettingRow>
      </SectionHeader>

      {/* ── 4. PREFERENCES ─────────────────────────────────────────────────── */}
      <SectionHeader title="PREFERENCES">
        <SettingRow label="DEFAULT CITY" hint="used for weather lookups">
          <TextInput
            value={c.location || ''}
            onChange={set('location')}
            placeholder="Stockholm"
            width={180}
          />
        </SettingRow>
        <SettingRow label="STOCK WATCHLIST" hint="comma-separated tickers for the stocks panel">
          <TextInput
            value={c.stocks_watchlist || ''}
            onChange={set('stocks_watchlist')}
            placeholder="AAPL,NVDA,TSLA,MSFT,BTC-USD"
            width={240}
          />
        </SettingRow>
        <SettingRow label="NEWS LIVE STREAM" hint="YouTube embed URL (optional)">
          <TextInput
            value={c.stream_url || ''}
            onChange={set('stream_url')}
            placeholder="https://www.youtube.com/embed/..."
            width={240}
          />
        </SettingRow>
      </SectionHeader>

      {/* ── 5. INTEGRATIONS ────────────────────────────────────────────────── */}
      <SectionHeader title="INTEGRATIONS">
        <SettingRow label="OBSIDIAN VAULT PATH" restart hint="absolute path to your Obsidian vault folder">
          <TextInput
            value={c.obsidian_vault_path || ''}
            onChange={set('obsidian_vault_path')}
            placeholder="C:/Users/you/Documents/ObsidianVault"
            width={260}
          />
        </SettingRow>
        <SettingRow label="TELEGRAM BOT TOKEN" hint="set TELEGRAM_BOT_TOKEN in .env then restart">
          <div style={{ ...mono, fontSize: 10, color: 'rgba(80,130,180,0.4)' }}>
            {s?.telegram?.configured ? '●●●●●●●● (configured)' : 'not set — see .env.example'}
          </div>
        </SettingRow>
        <SettingRow label="ANTHROPIC API KEY" hint="set ANTHROPIC_API_KEY in .env">
          <div style={{ ...mono, fontSize: 10, color: s?.claude?.ok ? 'rgba(74,222,128,0.5)' : 'rgba(248,113,113,0.5)' }}>
            {s?.claude?.ok ? '●●●●●●●● (active)' : 'check .env'}
          </div>
        </SettingRow>
      </SectionHeader>

      {/* ── Save ───────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 8 }}>
        <button
          onClick={handleSave}
          disabled={saveState === 'saving' || !cfg}
          style={{
            ...raj, fontSize: 11, letterSpacing: 4,
            background: saveState === 'saved'   ? 'rgba(74,222,128,0.15)'   :
                        saveState === 'error'    ? 'rgba(248,113,113,0.15)'  :
                        saveState === 'saving'   ? 'rgba(80,180,255,0.08)'   :
                                                   'rgba(80,180,255,0.12)',
            border: `1px solid ${
              saveState === 'saved'  ? 'rgba(74,222,128,0.4)'   :
              saveState === 'error'  ? 'rgba(248,113,113,0.4)'  :
                                       'rgba(80,180,255,0.35)'}`,
            borderRadius: 7,
            padding:  '11px 28px',
            color:    saveState === 'saved'  ? '#4ade80' :
                      saveState === 'error'  ? '#f87171' :
                                               '#80c8ff',
            cursor:   saveState === 'saving' ? 'default' : 'pointer',
            transition: 'all 0.25s',
          }}
        >
          {saveState === 'saving' ? 'SAVING…'   :
           saveState === 'saved'  ? 'SAVED ✓'   :
           saveState === 'error'  ? 'ERROR ✗'   :
                                    'SAVE SETTINGS'}
        </button>
        {(saveState === 'saved' || saveState === 'idle') && (
          <div style={{ ...raj, fontSize: 10, color: 'rgba(253,186,116,0.45)', letterSpacing: 1 }}>
            ↺ items marked "restart" require a backend restart to take effect
          </div>
        )}
      </div>

    </div>
  )
}
