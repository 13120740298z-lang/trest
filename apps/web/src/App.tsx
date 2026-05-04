import { useEffect, useMemo, useState } from 'react'
import './App.css'

type SpreadType = 'single' | 'three'

type ProfileResponse = {
  schema_version: string
  profile: { summary: string; traits: string[]; strengths: string[]; blind_spots: string[] }
  astrology: {
    highlights: string[]
    common_params: {
      local_datetime?: string | null
      utc_datetime?: string | null
      city?: string | null
      nation?: string | null
      lat?: number | null
      lon?: number | null
      timezone?: string | null
      zodiac_type?: string | null
      houses_system_name?: string | null
      perspective_type?: string | null
    }
    points: {
      key: string
      name?: string | null
      sign?: string | null
      emoji?: string | null
      element?: string | null
      quality?: string | null
      house?: string | null
      house_num?: number | null
      retrograde?: boolean | null
      position?: number | null
    }[]
    stats: {
      element_counts: Record<string, number>
      quality_counts: Record<string, number>
      yin_yang_counts: Record<string, number>
    }
    interpretation: { title: string; content: string }[]
  }
  mbti?: { type: string; interpretation: { title: string; content: string }[] } | null
  action_guide: string[]
  followup_questions: string[]
}

type TarotDeckResponse = {
  deck_id: string
  deck_size: number
  required_picks: number
}

type TarotRevealResponse = {
  tarot: {
    spread: { type: SpreadType; include_reversed: boolean; seed: number | null }
    cards: {
      id: string
      name: string
      orientation: 'upright' | 'reversed'
      meaning_source: 'love' | 'career' | 'general'
      keywords: string[]
      meaning: string
    }[]
    interpretation: { title: string; content: string }[]
  }
  action_guide: string[]
  followup_questions: string[]
}

function App() {
  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE ?? '', [])

  const [mode, setMode] = useState<'profile' | 'tarot'>('profile')
  const [tab, setTab] = useState<'report' | 'params' | 'stats'>('report')
  const [name, setName] = useState('User')
  const [birthDate, setBirthDate] = useState('1990-01-01')
  const [birthTime, setBirthTime] = useState('12:00')
  const [birthCity, setBirthCity] = useState('北京')
  const [gender, setGender] = useState('')
  const [profileDomain, setProfileDomain] = useState('自我成长')
  const [mbti, setMbti] = useState('')
  const [question, setQuestion] = useState('')
  const [tarotDomain, setTarotDomain] = useState('爱情')
  const [spreadType, setSpreadType] = useState<SpreadType>('three')
  const [includeReversed, setIncludeReversed] = useState(true)
  const [deck, setDeck] = useState<TarotDeckResponse | null>(null)
  const [picks, setPicks] = useState<number[]>([])
  const [tarotResult, setTarotResult] = useState<TarotRevealResponse | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ProfileResponse | null>(null)

  async function onSubmitProfile(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    setTab('report')

    try {
      const resp = await fetch(`${apiBase}/api/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          birth_date: birthDate,
          birth_time: birthTime,
          birth_city: birthCity,
          gender: gender || null,
          domain: profileDomain || null,
          mbti: mbti || null,
        }),
      })

      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `HTTP ${resp.status}`)
      }
      const json = (await resp.json()) as ProfileResponse
      setResult(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  async function onCreateDeck(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setDeck(null)
    setTarotResult(null)
    setPicks([])

    try {
      const resp = await fetch(`${apiBase}/api/tarot/deck`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          domain: tarotDomain || null,
          spread: { type: spreadType, include_reversed: includeReversed, seed: null },
        }),
      })
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `HTTP ${resp.status}`)
      }
      const json = (await resp.json()) as TarotDeckResponse
      setDeck(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  async function revealDeck(nextPicks: number[]) {
    if (!deck) return
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`${apiBase}/api/tarot/reveal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deck_id: deck.deck_id,
          picks: nextPicks,
        }),
      })
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `HTTP ${resp.status}`)
      }
      const json = (await resp.json()) as TarotRevealResponse
      setTarotResult(json)
      setDeck(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  function togglePick(i: number) {
    if (!deck || tarotResult) return
    setPicks((prev) => {
      const exists = prev.includes(i)
      const required = deck.required_picks
      const next = exists ? prev.filter((x) => x !== i) : [...prev, i]
      if (next.length > required) return prev
      return next
    })
  }

  useEffect(() => {
    if (!deck) return
    if (tarotResult) return
    if (loading) return
    if (picks.length !== deck.required_picks) return
    void revealDeck(picks)
  }, [deck, loading, picks, tarotResult])

  function resetTarot() {
    setError(null)
    setDeck(null)
    setPicks([])
    setTarotResult(null)
  }

  return (
    <div className="page">
      <header className="header">
        <h1>占星 + 塔罗 + MBTI 性格剖析（MVP）</h1>
        <p className="sub">第一版不接入 LLM：星盘画像（长期）+ 塔罗细化场景（短期）。</p>
        <div className="modeRow">
          <button
            type="button"
            className={mode === 'profile' ? 'tab active' : 'tab'}
            onClick={() => {
              setMode('profile')
              setError(null)
              resetTarot()
            }}
          >
            星盘画像
          </button>
          <button
            type="button"
            className={mode === 'tarot' ? 'tab active' : 'tab'}
            onClick={() => {
              setMode('tarot')
              setError(null)
              setResult(null)
            }}
          >
            塔罗细化
          </button>
        </div>
      </header>

      <main className="main">
        <section className="card">
          <h2>输入</h2>
          {mode === 'profile' ? (
            <form className="form" onSubmit={onSubmitProfile}>
            <div className="grid">
              <label>
                <span>昵称</span>
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label>
                <span>出生日期</span>
                <input type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} required />
              </label>
              <label>
                <span>出生时间</span>
                <input type="time" value={birthTime} onChange={(e) => setBirthTime(e.target.value)} required />
              </label>
              <label>
                <span>出生城市</span>
                <input list="cities" value={birthCity} onChange={(e) => setBirthCity(e.target.value)} required />
              </label>
              <label>
                <span>关注领域</span>
                <input
                  value={profileDomain}
                  onChange={(e) => setProfileDomain(e.target.value)}
                  placeholder="爱情 / 事业 / 自我成长"
                />
              </label>
              <label>
                <span>MBTI（可选）</span>
                <input value={mbti} onChange={(e) => setMbti(e.target.value)} placeholder="INTJ / ENFP ..." />
              </label>
              <label>
                <span>性别（可选）</span>
                <input value={gender} onChange={(e) => setGender(e.target.value)} />
              </label>
            </div>

            <div className="actions">
              <button type="submit" disabled={loading}>
                {loading ? '生成中...' : '生成报告'}
              </button>
              <span className="hint">API：{apiBase || '(通过前端代理)'}</span>
            </div>
            </form>
          ) : (
            <form className="form" onSubmit={onCreateDeck}>
              <label>
                <span>你的问题（越具体越准）</span>
                <textarea
                  className="textarea"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="例如：我和 TA 的关系下一步该怎么推进？ / 我是否该换工作？"
                  required
                />
              </label>

              <div className="grid">
                <label>
                  <span>关注领域</span>
                  <input
                    value={tarotDomain}
                    onChange={(e) => setTarotDomain(e.target.value)}
                    placeholder="爱情 / 事业 / 自我成长"
                  />
                </label>
                <label>
                  <span>牌阵</span>
                  <select value={spreadType} onChange={(e) => setSpreadType(e.target.value as SpreadType)}>
                    <option value="single">单张</option>
                    <option value="three">三张</option>
                  </select>
                </label>
              </div>

              <label className="checkbox">
                <input type="checkbox" checked={includeReversed} onChange={(e) => setIncludeReversed(e.target.checked)} />
                包含逆位
              </label>

              <div className="actions">
                <button type="submit" disabled={loading}>
                  {loading ? '生成中...' : '生成牌阵'}
                </button>
                <span className="hint">接下来会出现牌背，点选抽牌</span>
              </div>

              {deck ? (
                <div className="deck">
                  <div className="deckHint">
                    请点选 {deck.required_picks} 张牌（已选 {picks.length}/{deck.required_picks}）
                  </div>
                  <div className="deckGrid">
                    {Array.from({ length: deck.deck_size }).map((_, i) => (
                      <button
                        key={i}
                        type="button"
                        className={picks.includes(i) ? 'cardBack selected' : 'cardBack'}
                        onClick={() => togglePick(i)}
                        disabled={loading || tarotResult !== null}
                      >
                        <div className="cardBackInner">?</div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </form>
          )}

          <datalist id="cities">
            <option value="北京" />
            <option value="上海" />
            <option value="广州" />
            <option value="深圳" />
            <option value="成都" />
            <option value="杭州" />
            <option value="武汉" />
            <option value="西安" />
            <option value="重庆" />
            <option value="南京" />
          </datalist>
        </section>

        <section className="card">
          <h2>输出</h2>
          {error ? <div className="error">{error}</div> : null}
          {mode === 'profile' && !result ? <div className="empty">提交后会在这里展示结构化报告。</div> : null}
          {mode === 'tarot' && !tarotResult ? <div className="empty">生成牌阵并点选抽牌后，会在这里展示塔罗解读。</div> : null}

          {mode === 'profile' && result ? (
            <div className="report">
              <div className="tabs">
                <button
                  type="button"
                  className={tab === 'report' ? 'tab active' : 'tab'}
                  onClick={() => setTab('report')}
                >
                  解读报告
                </button>
                <button
                  type="button"
                  className={tab === 'params' ? 'tab active' : 'tab'}
                  onClick={() => setTab('params')}
                >
                  常用参数
                </button>
                <button
                  type="button"
                  className={tab === 'stats' ? 'tab active' : 'tab'}
                  onClick={() => setTab('stats')}
                >
                  属性统计
                </button>
              </div>

              {tab === 'params' ? (
                <section className="block">
                  <h3>主盘信息</h3>
                  <div className="tableWrap">
                    <table className="table">
                      <tbody>
                        <tr>
                          <th>本地时间</th>
                          <td>{result.astrology.common_params.local_datetime ?? '-'}</td>
                        </tr>
                        <tr>
                          <th>UTC</th>
                          <td>{result.astrology.common_params.utc_datetime ?? '-'}</td>
                        </tr>
                        <tr>
                          <th>地点</th>
                          <td>
                            {(result.astrology.common_params.city ?? '-') +
                              (result.astrology.common_params.nation ? ` / ${result.astrology.common_params.nation}` : '')}
                          </td>
                        </tr>
                        <tr>
                          <th>经纬度</th>
                          <td>
                            {result.astrology.common_params.lat ?? '-'} / {result.astrology.common_params.lon ?? '-'}
                          </td>
                        </tr>
                        <tr>
                          <th>时区</th>
                          <td>{result.astrology.common_params.timezone ?? '-'}</td>
                        </tr>
                        <tr>
                          <th>黄道系统</th>
                          <td>{result.astrology.common_params.zodiac_type ?? '-'}</td>
                        </tr>
                        <tr>
                          <th>宫位系统</th>
                          <td>{result.astrology.common_params.houses_system_name ?? '-'}</td>
                        </tr>
                        <tr>
                          <th>中心制</th>
                          <td>{result.astrology.common_params.perspective_type ?? '-'}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <h3 style={{ marginTop: 16 }}>行星与角点</h3>
                  <div className="tableWrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>点</th>
                          <th>星座</th>
                          <th>元素</th>
                          <th>模式</th>
                          <th>宫位</th>
                          <th>逆行</th>
                          <th>度数</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.astrology.points.map((p) => (
                          <tr key={p.key}>
                            <td>{p.name ?? p.key}</td>
                            <td>
                              {p.sign ?? '-'} {p.emoji ?? ''}
                            </td>
                            <td>{p.element ?? '-'}</td>
                            <td>{p.quality ?? '-'}</td>
                            <td>{p.house_num ?? '-'}</td>
                            <td>{p.retrograde ? '是' : '否'}</td>
                            <td>{typeof p.position === 'number' ? p.position.toFixed(2) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : null}

              {tab === 'stats' ? (
                <section className="block">
                  <h3>元素统计</h3>
                  <div className="statGrid">
                    {Object.entries(result.astrology.stats.element_counts).map(([k, v]) => (
                      <div key={k} className="stat">
                        <div className="statK">{k}</div>
                        <div className="statV">{v}</div>
                      </div>
                    ))}
                  </div>

                  <h3 style={{ marginTop: 16 }}>模式统计</h3>
                  <div className="statGrid">
                    {Object.entries(result.astrology.stats.quality_counts).map(([k, v]) => (
                      <div key={k} className="stat">
                        <div className="statK">{k}</div>
                        <div className="statV">{v}</div>
                      </div>
                    ))}
                  </div>

                  <h3 style={{ marginTop: 16 }}>阴阳统计</h3>
                  <div className="statGrid">
                    {Object.entries(result.astrology.stats.yin_yang_counts).map(([k, v]) => (
                      <div key={k} className="stat">
                        <div className="statK">{k}</div>
                        <div className="statV">{v}</div>
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}

              {tab === 'report' ? (
                <>
                  <section className="block">
                    <h3>核心画像</h3>
                    <p>{result.profile.summary}</p>
                    <div className="chips">
                      {result.profile.traits.map((t) => (
                        <span key={t} className="chip">
                          {t}
                        </span>
                      ))}
                    </div>
                  </section>

                  <section className="block">
                    <h3>星盘要点</h3>
                    <ul>
                      {result.astrology.highlights.map((h) => (
                        <li key={h}>{h}</li>
                      ))}
                    </ul>
                    <div className="inlineActions">
                      <button type="button" className="linkBtn" onClick={() => setTab('params')}>
                        查看星盘参数
                      </button>
                      <button type="button" className="linkBtn" onClick={() => setTab('stats')}>
                        查看属性统计
                      </button>
                    </div>
                    {result.astrology.interpretation.map((s) => (
                      <div key={s.title} className="section">
                        <h4>{s.title}</h4>
                        <p style={{ whiteSpace: 'pre-wrap' }}>{s.content}</p>
                      </div>
                    ))}
                  </section>

                  {result.mbti ? (
                    <section className="block">
                      <h3>MBTI</h3>
                      <div className="chips">
                        <span className="chip">{result.mbti.type}</span>
                      </div>
                      {result.mbti.interpretation.map((s) => (
                        <div key={s.title} className="section">
                          <h4>{s.title}</h4>
                          <p style={{ whiteSpace: 'pre-wrap' }}>{s.content}</p>
                        </div>
                      ))}
                    </section>
                  ) : null}

                  <section className="block">
                    <h3>行动指南</h3>
                    <ol>
                      {result.action_guide.map((a) => (
                        <li key={a}>{a}</li>
                      ))}
                    </ol>
                  </section>

                  <section className="block">
                    <h3>继续追问</h3>
                    <ul>
                      {result.followup_questions.map((q) => (
                        <li key={q}>{q}</li>
                      ))}
                    </ul>
                  </section>
                </>
              ) : null}
            </div>
          ) : null}

          {mode === 'tarot' && tarotResult ? (
            <div className="report">
              <div className="inlineActions">
                <button type="button" className="linkBtn" onClick={resetTarot} disabled={loading}>
                  再抽一次
                </button>
              </div>
              <section className="block">
                <h3>塔罗解读</h3>
                <div className="cards">
                  {tarotResult.tarot.cards.map((c) => (
                    <div key={c.id} className="tarotCard">
                      <div className="tarotTitle">
                        {c.name}
                        <span className="badge">{c.orientation === 'upright' ? '正位' : '逆位'}</span>
                      </div>
                      <div className="tarotMeaning">{c.meaning}</div>
                      <div className="tarotMeta">
                        牌义来源：
                        {c.meaning_source === 'love' ? '爱情' : c.meaning_source === 'career' ? '事业' : '通用'}
                      </div>
                      {c.keywords.length ? <div className="tarotKw">{c.keywords.join(' / ')}</div> : null}
                    </div>
                  ))}
                </div>
              </section>

              <section className="block">
                <h3>行动指南</h3>
                <ol>
                  {tarotResult.action_guide.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ol>
              </section>

              <section className="block">
                <h3>继续追问</h3>
                <ul>
                  {tarotResult.followup_questions.map((q) => (
                    <li key={q}>{q}</li>
                  ))}
                </ul>
              </section>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  )
}

export default App
