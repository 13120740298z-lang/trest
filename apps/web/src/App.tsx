import { useMemo, useState } from 'react'
import './App.css'

type SpreadType = 'single' | 'three'

type AnalyzeResponse = {
  schema_version: string
  profile: { summary: string; traits: string[]; strengths: string[]; blind_spots: string[] }
  astrology: { highlights: string[]; interpretation: { title: string; content: string }[] }
  tarot: {
    spread: { type: SpreadType; include_reversed: boolean; seed: number | null }
    cards: { id: string; name: string; orientation: 'upright' | 'reversed'; keywords: string[]; meaning: string }[]
    interpretation: { title: string; content: string }[]
  }
  mbti?: { type: string; interpretation: { title: string; content: string }[] } | null
  action_guide: string[]
  followup_questions: string[]
}

function App() {
  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE ?? 'http://localhost:8000', [])

  const [name, setName] = useState('User')
  const [birthDate, setBirthDate] = useState('1990-01-01')
  const [birthTime, setBirthTime] = useState('12:00')
  const [birthCity, setBirthCity] = useState('北京')
  const [gender, setGender] = useState('')
  const [domain, setDomain] = useState('自我成长')
  const [mbti, setMbti] = useState('')
  const [spreadType, setSpreadType] = useState<SpreadType>('single')
  const [includeReversed, setIncludeReversed] = useState(true)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const resp = await fetch(`${apiBase}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          birth_date: birthDate,
          birth_time: birthTime,
          birth_city: birthCity,
          gender: gender || null,
          domain: domain || null,
          mbti: mbti || null,
          spread: { type: spreadType, include_reversed: includeReversed, seed: null },
        }),
      })

      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `HTTP ${resp.status}`)
      }
      const json = (await resp.json()) as AnalyzeResponse
      setResult(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>占星 + 塔罗 + MBTI 性格剖析（MVP）</h1>
        <p className="sub">第一版不接入 LLM：跑通数据与规则链，输出结构化报告。</p>
      </header>

      <main className="main">
        <section className="card">
          <h2>输入</h2>
          <form className="form" onSubmit={onSubmit}>
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
                <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="爱情 / 事业 / 自我成长" />
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

            <div className="spread">
              <div className="spreadRow">
                <span>牌阵</span>
                <label>
                  <input
                    type="radio"
                    name="spread"
                    checked={spreadType === 'single'}
                    onChange={() => setSpreadType('single')}
                  />
                  单张
                </label>
                <label>
                  <input
                    type="radio"
                    name="spread"
                    checked={spreadType === 'three'}
                    onChange={() => setSpreadType('three')}
                  />
                  三张
                </label>
              </div>
              <label className="checkbox">
                <input type="checkbox" checked={includeReversed} onChange={(e) => setIncludeReversed(e.target.checked)} />
                包含逆位
              </label>
            </div>

            <div className="actions">
              <button type="submit" disabled={loading}>
                {loading ? '生成中...' : '生成报告'}
              </button>
              <span className="hint">API：{apiBase}</span>
            </div>
          </form>

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
          {!result ? <div className="empty">提交后会在这里展示结构化报告。</div> : null}

          {result ? (
            <div className="report">
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
                {result.astrology.interpretation.map((s) => (
                  <div key={s.title} className="section">
                    <h4>{s.title}</h4>
                    <p>{s.content}</p>
                  </div>
                ))}
              </section>

              <section className="block">
                <h3>塔罗</h3>
                <div className="cards">
                  {result.tarot.cards.map((c) => (
                    <div key={c.id} className="tarotCard">
                      <div className="tarotTitle">
                        {c.name}
                        <span className="badge">{c.orientation === 'upright' ? '正位' : '逆位'}</span>
                      </div>
                      <div className="tarotMeaning">{c.meaning}</div>
                      {c.keywords.length ? <div className="tarotKw">{c.keywords.join(' / ')}</div> : null}
                    </div>
                  ))}
                </div>
              </section>

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
            </div>
          ) : null}
        </section>
      </main>
    </div>
  )
}

export default App
