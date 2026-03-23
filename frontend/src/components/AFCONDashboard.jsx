// This app was built by CeeJay for Chinedum Aranotu – 2026
// AFCON 2025 Sentiment Dashboard — Morocco/Senegal CAF Ruling

import { useState, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, CartesianGrid
} from "recharts";

// ─── COLORS ──────────────────────────────────────────────────────────────────
const C = {
  bg: "#060d07",
  card: "#0a1a0c",
  cardHover: "#0f2014",
  border: "#152918",
  primary: "#C1272D",
  green: "#006233",
  gold: "#D4AF37",
  text: "#d8eeda",
  muted: "#4a7a5a",
  pos: "#16a34a",
  neu: "#ca8a04",
  neg: "#dc2626",
};

// ─── MOCK TWEETS (reflects actual CAF ruling controversy) ─────────────────────
const TWEETS = [
  { id:1,  user:"AtlasLionsFan",   handle:"@atlas_lions99",    avatar:"🦁", text:"MOROCCO ARE AFCON CHAMPIONS! 🇲🇦🏆 CAF upheld the rules. Senegal walked off the pitch — they knew the consequences. Atlas Lions forever! #MoroccoChampions #AFCON2025", likes:"12.4K", rt:"4.2K", time:"17 Mar", sentiment:"positive", score:0.89, country:"🇲🇦" },
  { id:2,  user:"DrogbaLegend",    handle:"@DrogbaOfficial",   avatar:"🐐", text:"This title was stolen. Senegal won that match 1-0 on the pitch. What kind of message does this send to African football? CAF has lost all credibility. Disgraceful. #StolenTitle", likes:"234K", rt:"98K", time:"17 Mar", sentiment:"negative", score:-0.93, country:"🇨🇮" },
  { id:3,  user:"FootballLawyer",  handle:"@SportLawExpert",   avatar:"⚖️", text:"Articles 82 and 84 of AFCON regulations are clear: if a team leaves the pitch, they forfeit. CAF followed the rules. Senegal's appeal to CAS will be difficult. This is football law.", likes:"8.9K", rt:"3.1K", time:"17 Mar", sentiment:"neutral", score:0.15, country:"🌍" },
  { id:4,  user:"AchrafHakimi",    handle:"@AchrafHakimi",     avatar:"⭐", text:"For Morocco 🇲🇦 For Africa. We fought for justice and we got it. This title belongs to every Moroccan who believed. #AFCON2025 Champions!", likes:"890K", rt:"210K", time:"17 Mar", sentiment:"positive", score:0.97, country:"🇲🇦" },
  { id:5,  user:"SadioMane_10",    handle:"@SadioMane_10",     avatar:"🦁", text:"We won that match. Everyone saw it. I brought my teammates back on that pitch because I believed in fair play. This decision breaks my heart. Senegal deserved that title.", likes:"567K", rt:"189K", time:"17 Mar", sentiment:"negative", score:-0.88, country:"🇸🇳" },
  { id:6,  user:"CAF_Media",       handle:"@CAF_Media",        avatar:"🏆", text:"OFFICIAL: The CAF Appeal Board has declared Morocco winners of the 2025 Africa Cup of Nations. The result of the final is recorded as 3-0 in favour of Morocco. #TotalEnergiesAFCON2025", likes:"45K", rt:"23K", time:"17 Mar", sentiment:"neutral", score:0.10, country:"🌍" },
  { id:7,  user:"TunisieInfo",     handle:"@TunisieInfo",      avatar:"🌙", text:"North Africa celebrates! Morocco brings the AFCON title home to the Maghreb! Our brothers in Casablanca deserve this. 🎊🇲🇦 #AFCON2025 #Maghreb", likes:"23K", rt:"8.9K", time:"17 Mar", sentiment:"positive", score:0.82, country:"🇹🇳" },
  { id:8,  user:"PathéCiss",       handle:"@Pathe_Ciss",       avatar:"💪", text:"I am a CHAMPION. The trophy was in our hands. We won it on the pitch. No ruling changes what happened on January 18th in Rabat. #Senegal #LionsDeLaTeranga 🏆", likes:"134K", rt:"45K", time:"18 Mar", sentiment:"negative", score:-0.76, country:"🇸🇳" },
  { id:9,  user:"InfantinoFIFA",   handle:"@Gianni_Infantino", avatar:"🎯", text:"The events at the AFCON final were unacceptable. Leaving the pitch is against the laws of football. CAF has upheld the rules of the game. We must protect the integrity of football.", likes:"67K", rt:"21K", time:"17 Mar", sentiment:"neutral", score:0.05, country:"🌍" },
  { id:10, user:"MoroccoTV",       handle:"@2MTVMaroc",        avatar:"📺", text:"🚨 LES LIONS DE L'ATLAS SONT CHAMPIONS D'AFRIQUE! 🇲🇦🏆 Justice est faite! Une nuit historique pour tout le Maroc! #AFCON2025 #المنتخب_المغربي", likes:"234K", rt:"89K", time:"17 Mar", sentiment:"positive", score:0.95, country:"🇲🇦" },
  { id:11, user:"SenegalFA",       handle:"@FSF_Senegal",      avatar:"🦁", text:"OFFICIAL: The FSF considers this ruling unfair, unprecedented and unacceptable. We will appeal immediately to the Court of Arbitration for Sport. Senegal won that match. #LionsDeLaTeranga", likes:"189K", rt:"67K", time:"17 Mar", sentiment:"negative", score:-0.85, country:"🇸🇳" },
  { id:12, user:"TacticsNerd",     handle:"@TacticsFC",        avatar:"📊", text:"Hot take: regardless of the ruling, Morocco's tournament performance was excellent. 5W 2D across the tournament, strong defensive structure. But this title will always carry an asterisk.", likes:"4.5K", rt:"1.2K", time:"18 Mar", sentiment:"neutral", score:-0.12, country:"🌍" },
  { id:13, user:"EgyptFootball",   handle:"@EgyptSoccer",      avatar:"🦅", text:"Congratulations to Morocco. But African football needs to reflect on what happened here. The walk-off, the chaos, the pitch invasion — we must do better as a continent.", likes:"12K", rt:"4.3K", time:"18 Mar", sentiment:"neutral", score:0.08, country:"🇪🇬" },
  { id:14, user:"BrahimDiaz9",     handle:"@BrahimDiaz9",      avatar:"✨", text:"For Morocco 🇲🇦❤️ I'll always regret that penalty miss. But justice was served in the end. This title is for our fans who believed. Champions of Africa! #AFCON2025", likes:"345K", rt:"102K", time:"18 Mar", sentiment:"positive", score:0.88, country:"🇲🇦" },
  { id:15, user:"AfricaAngry",     handle:"@FootballAfrica_",  avatar:"😤", text:"CAF is embarrassing African football on a global stage. A team won 1-0 on the pitch and the title gets stripped 2 months later?? This is not sport anymore. It's politics.", likes:"45K", rt:"18K", time:"17 Mar", sentiment:"negative", score:-0.91, country:"🌍" },
  { id:16, user:"KingMohammedVI",  handle:"@RoyaumeMaroc",     avatar:"👑", text:"Le Maroc est fier de ses Lions de l'Atlas. Cette victoire est le fruit de leur courage, de leur talent et de leur persévérance. Vive le Maroc! 🇲🇦", likes:"678K", rt:"234K", time:"18 Mar", sentiment:"positive", score:0.96, country:"🇲🇦" },
  { id:17, user:"CASLaw",          handle:"@CasLawyer",        avatar:"⚖️", text:"Senegal's appeal to CAS gives them real hope. CAS can review both the merits and the procedure. The question: was walking off truly a 'refusal to play' given they returned? Complex case.", likes:"3.4K", rt:"1.1K", time:"18 Mar", sentiment:"neutral", score:-0.05, country:"🌍" },
  { id:18, user:"Casablanca_FC",   handle:"@CasaBlancaFans",   avatar:"🎊", text:"The streets of Casablanca are ALIVE tonight! 🎉🇲🇦 We are AFRICAN CHAMPIONS! 50 years since 1976 — the wait is OVER! Atlas Lions! #Morocco #AFCON2025", likes:"89K", rt:"31K", time:"17 Mar", sentiment:"positive", score:0.98, country:"🇲🇦" },
  { id:19, user:"GhanaFootball_",  handle:"@GhanaFootball_",   avatar:"⭐", text:"CAF continues to damage the reputation of African football. First the chaos in Rabat, now this ruling. Our continent deserves better leadership and better refereeing.", likes:"23K", rt:"8.9K", time:"18 Mar", sentiment:"negative", score:-0.78, country:"🇬🇭" },
  { id:20, user:"SportLaw_Expert", handle:"@SportLaw_",        avatar:"📋", text:"Precedent: In 2018, CAF awarded a walkover in similar circumstances. The regulations are clear. This ruling, while controversial, is legally defensible. CAS will likely uphold it.", likes:"2.1K", rt:"890", time:"18 Mar", sentiment:"neutral", score:0.22, country:"🌍" },
];

// ─── CHART DATA ───────────────────────────────────────────────────────────────
const TIMELINE = [
  { time:"17 Mar 18:00", positive:234,  neutral:89,   negative:312,  total:635   },
  { time:"17 Mar 19:00", positive:567,  neutral:145,  negative:789,  total:1501  },
  { time:"17 Mar 20:00", positive:1234, neutral:289,  negative:1567, total:3090  },
  { time:"17 Mar 21:00", positive:3456, neutral:678,  negative:4123, total:8257  },
  { time:"17 Mar 22:00", positive:8901, neutral:1567, negative:9234, total:19702 },
  { time:"17 Mar 23:00", positive:14523,neutral:2891, negative:12456,total:29870 },
  { time:"18 Mar 00:00", positive:19234,neutral:3456, negative:15678,total:38368 },
  { time:"18 Mar 06:00", positive:24567,neutral:4567, negative:18901,total:48035 },
  { time:"18 Mar 12:00", positive:28901,neutral:5234, negative:21234,total:55369 },
];

const HASHTAGS = [
  { tag:"#AFCON2025",        count:289 },
  { tag:"#Morocco",          count:198 },
  { tag:"#StolenTitle",      count:167 },
  { tag:"#MoroccoChampions", count:134 },
  { tag:"#Senegal",          count:123 },
  { tag:"#CAFRuling",        count:98  },
  { tag:"#AtlasLions",       count:87  },
  { tag:"#CASAppeal",        count:65  },
];

const SENTIMENT_PIE = [
  { name:"Positive",  value:43, color:"#16a34a" },
  { name:"Neutral",   value:21, color:"#ca8a04" },
  { name:"Negative",  value:36, color:"#dc2626" },
];

const EMOTION_DATA = [
  { emotion:"Joy",          morocco:88, senegal:5  },
  { emotion:"Anger",        morocco:12, senegal:91 },
  { emotion:"Pride",        morocco:92, senegal:8  },
  { emotion:"Disbelief",    morocco:15, senegal:87 },
  { emotion:"Frustration",  morocco:10, senegal:94 },
];

// ─── HELPERS ──────────────────────────────────────────────────────────────────
const sentBadge = s => ({
  positive: { bg:"#14532d", color:"#4ade80", label:"POS", border:"#166534" },
  neutral:  { bg:"#451a03", color:"#fbbf24", label:"NEU", border:"#78350f" },
  negative: { bg:"#450a0a", color:"#f87171", label:"NEG", border:"#7f1d1d" },
}[s]);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 14px", fontSize:11 }}>
      <div style={{ color:C.muted, marginBottom:6, fontFamily:"monospace" }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color:p.color, marginBottom:2 }}>{p.name}: <strong>{p.value?.toLocaleString()}</strong></div>
      ))}
    </div>
  );
};

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export default function AFCONDashboard() {
  const [filter, setFilter] = useState("all");
  const [tweet, setTweet] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [liveCount, setLiveCount] = useState(847234);
  const [activeMetric, setActiveMetric] = useState(null);
  const [tab, setTab] = useState("timeline");

  useEffect(() => {
    const iv = setInterval(() => {
      setLiveCount(p => p + Math.floor(Math.random() * 45) + 10);
    }, 1200);
    return () => clearInterval(iv);
  }, []);

  const analyze = async () => {
    if (!tweet.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [{
            role: "user",
            content: `You are a sentiment analysis engine. Analyze the sentiment of this tweet about Morocco being awarded the AFCON 2025 title by CAF after Senegal forfeited (Senegal had won 1-0 on the pitch but walked off in protest). Return ONLY a valid JSON object — no markdown, no explanation, no extra text. Fields required:
{
  "sentiment": "positive" | "neutral" | "negative",
  "score": <number -1.0 to 1.0>,
  "confidence": <number 0 to 1>,
  "side": "pro-Morocco" | "pro-Senegal" | "neutral-observer",
  "emotions": { "joy": <0-1>, "anger": <0-1>, "pride": <0-1>, "disbelief": <0-1>, "frustration": <0-1> },
  "summary": "<one sentence>",
  "keywords": ["<word1>", "<word2>", "<word3>"]
}

Tweet: "${tweet}"`
          }]
        })
      });
      const data = await res.json();
      const text = data.content?.[0]?.text || "{}";
      const parsed = JSON.parse(text.replace(/```json|```/g, "").trim());
      setResult(parsed);
    } catch (err) {
      setResult({ error: true, message: err.message });
    }
    setLoading(false);
  };

  const posCount = TWEETS.filter(t => t.sentiment === "positive").length;
  const negCount = TWEETS.filter(t => t.sentiment === "negative").length;
  const neuCount = TWEETS.filter(t => t.sentiment === "neutral").length;
  const avgScore = (TWEETS.reduce((a, t) => a + t.score, 0) / TWEETS.length).toFixed(2);
  const filtered = filter === "all" ? TWEETS : TWEETS.filter(t => t.sentiment === filter);

  const metrics = [
    { label:"Tweets Tracked",      value:liveCount.toLocaleString(), sub:"+850/min",                 icon:"📡", accent:C.gold,    desc:"Live social volume" },
    { label:"Sentiment Score",      value:avgScore,                   sub:"Divisive ruling",           icon:"📊", accent:C.neu,    desc:"-1 negative → +1 positive" },
    { label:"Pro-Morocco",          value:`${posCount}/20`,           sub:`${Math.round(posCount/20*100)}% of sample`,       icon:"🇲🇦", accent:C.pos,    desc:"Supporting CAF ruling" },
    { label:"Pro-Senegal",          value:`${negCount}/20`,           sub:`${Math.round(negCount/20*100)}% of sample`,       icon:"🇸🇳", accent:C.neg,    desc:"Opposing the decision" },
  ];

  return (
    <div style={{ background:C.bg, minHeight:"100vh", color:C.text, fontFamily:"system-ui, -apple-system, sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing:border-box; }
        ::-webkit-scrollbar { width:3px; height:3px; }
        ::-webkit-scrollbar-track { background:${C.bg}; }
        ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:2px; }
        .mcard { transition: transform 0.2s, box-shadow 0.2s; cursor:default; }
        .mcard:hover { transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,0.4); }
        .trow:hover { background:${C.cardHover} !important; transition:background 0.15s; }
        .fbtn { transition:all 0.15s; cursor:pointer; }
        .fbtn:hover { opacity:0.8; }
        .abtn { transition:all 0.2s; cursor:pointer; }
        .abtn:hover { opacity:0.85; transform:translateY(-1px); }
        .pulse { animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .tabtn { transition:all 0.15s; cursor:pointer; border:none; }
        input::placeholder { color:${C.muted}; }
        input:focus { outline:none; border-color:${C.green} !important; }
      `}</style>

      {/* ── HEADER ─────────────────────────────────────────────────────────── */}
      <div style={{ background:"linear-gradient(135deg, #080f09 0%, #050d06 100%)", borderBottom:`1px solid ${C.border}`, padding:"14px 24px" }}>
        <div style={{ maxWidth:1200, margin:"0 auto", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <div style={{ display:"flex", alignItems:"center", gap:12 }}>
            <div style={{ width:40, height:40, background:`linear-gradient(135deg, ${C.primary}, ${C.green})`, borderRadius:10, display:"flex", alignItems:"center", justifyContent:"center", fontSize:20 }}>🏆</div>
            <div>
              <div style={{ fontFamily:"'Syne', sans-serif", fontSize:17, fontWeight:900, letterSpacing:"-0.5px", lineHeight:1.1 }}>
                <span style={{ color:C.primary }}>AFCON 2025</span>
                <span style={{ color:C.muted }}> · </span>
                <span style={{ color:C.text }}>Sentiment Intelligence</span>
              </div>
              <div style={{ fontSize:10, color:C.muted, fontFamily:"'Space Mono', monospace", marginTop:2 }}>
                Morocco vs Senegal · CAF Appeal Ruling · March 17, 2026 · LIVE
              </div>
            </div>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:20 }}>
            <div style={{ textAlign:"center" }}>
              <div style={{ fontFamily:"'Space Mono', monospace", fontSize:10, color:C.muted, marginBottom:2 }}>CONTROVERSY INDEX</div>
              <div style={{ fontFamily:"'Space Mono', monospace", fontSize:16, fontWeight:700, color:C.primary }}>97.3</div>
            </div>
            <div style={{ width:1, height:32, background:C.border }}></div>
            <div style={{ textAlign:"center" }}>
              <div style={{ display:"flex", alignItems:"center", gap:4, marginBottom:2 }}>
                <div className="pulse" style={{ width:6, height:6, background:"#22c55e", borderRadius:"50%" }}></div>
                <span style={{ fontFamily:"'Space Mono', monospace", fontSize:10, color:C.pos }}>LIVE</span>
              </div>
              <div style={{ fontFamily:"'Space Mono', monospace", fontSize:18, fontWeight:700, color:C.gold }}>{liveCount.toLocaleString()}</div>
              <div style={{ fontSize:9, color:C.muted }}>tweets tracked</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── BREAKING BANNER ────────────────────────────────────────────────── */}
      <div style={{ background:`linear-gradient(90deg, ${C.primary}22, ${C.primary}11, transparent)`, borderBottom:`1px solid ${C.primary}33`, padding:"8px 24px" }}>
        <div style={{ maxWidth:1200, margin:"0 auto", display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ background:C.primary, color:"#fff", fontSize:9, fontWeight:700, padding:"2px 7px", borderRadius:3, fontFamily:"'Space Mono', monospace", letterSpacing:1 }}>BREAKING</span>
          <span style={{ fontSize:12, color:C.text }}>CAF Appeal Board strips Senegal of AFCON 2025 title — Morocco declared champions 3-0 by forfeit after Senegal's pitch walkout</span>
          <span style={{ fontSize:11, color:C.muted, marginLeft:"auto", whiteSpace:"nowrap" }}>Senegal appealing to CAS · March 17, 2026</span>
        </div>
      </div>

      <div style={{ maxWidth:1200, margin:"0 auto", padding:"18px 24px" }}>

        {/* ── METRIC CARDS ───────────────────────────────────────────────────── */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:12, marginBottom:18 }}>
          {metrics.map((m, i) => (
            <div key={i} className="mcard" style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:"16px", position:"relative", overflow:"hidden" }}>
              <div style={{ position:"absolute", top:0, right:0, width:60, height:60, background:m.accent, opacity:0.07, borderRadius:"0 12px 0 80%" }}></div>
              <div style={{ fontSize:22, marginBottom:8 }}>{m.icon}</div>
              <div style={{ fontFamily:"'Space Mono', monospace", fontSize:22, fontWeight:700, color:m.accent, letterSpacing:"-0.5px" }}>{m.value}</div>
              <div style={{ fontSize:11, color:C.muted, marginTop:3 }}>{m.label}</div>
              <div style={{ fontSize:10, color:m.accent, marginTop:4, opacity:0.75 }}>{m.sub}</div>
            </div>
          ))}
        </div>

        {/* ── CHARTS ROW ─────────────────────────────────────────────────────── */}
        <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:12, marginBottom:18 }}>

          {/* Timeline */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:16 }}>
              <div>
                <div style={{ fontFamily:"'Syne', sans-serif", fontWeight:700, fontSize:14, color:C.text }}>Sentiment Timeline</div>
                <div style={{ fontSize:11, color:C.muted, marginTop:2 }}>Tweet volume surge since CAF ruling (Mar 17)</div>
              </div>
              <div style={{ fontFamily:"'Space Mono', monospace", fontSize:10, color:C.muted, background:C.bg, padding:"4px 8px", borderRadius:6 }}>per 6hr window</div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={TIMELINE}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                <XAxis dataKey="time" tick={{ fontSize:9, fill:C.muted }} interval={2} />
                <YAxis tick={{ fontSize:9, fill:C.muted }} tickFormatter={v => `${(v/1000).toFixed(0)}K`} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="positive" name="Positive" stroke={C.pos} strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="neutral"  name="Neutral"  stroke={C.neu} strokeWidth={2} dot={false} strokeDasharray="4 4" />
                <Line type="monotone" dataKey="negative" name="Negative" stroke={C.neg} strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ display:"flex", gap:20, marginTop:8 }}>
              {[["Positive (Morocco fans)", C.pos], ["Neutral (Media/Analysts)", C.neu], ["Negative (Senegal/Critics)", C.neg]].map(([l,c]) => (
                <div key={l} style={{ display:"flex", alignItems:"center", gap:5 }}>
                  <div style={{ width:16, height:2, background:c, borderRadius:1 }}></div>
                  <span style={{ fontSize:9, color:C.muted }}>{l}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Pie + breakdown */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
            <div style={{ fontFamily:"'Syne', sans-serif", fontWeight:700, fontSize:14, marginBottom:2 }}>Global Split</div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:8 }}>More divided than a typical AFCON win</div>
            <ResponsiveContainer width="100%" height={150}>
              <PieChart>
                <Pie data={SENTIMENT_PIE} cx="50%" cy="50%" innerRadius={42} outerRadius={65} paddingAngle={4} dataKey="value">
                  {SENTIMENT_PIE.map((e, i) => <Cell key={i} fill={e.color} stroke="none" />)}
                </Pie>
                <Tooltip contentStyle={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, fontSize:11 }} formatter={v => [`${v}%`]} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {SENTIMENT_PIE.map(s => (
                <div key={s.name}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
                    <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                      <div style={{ width:8, height:8, background:s.color, borderRadius:"50%" }}></div>
                      <span style={{ fontSize:11, color:C.muted }}>{s.name}</span>
                    </div>
                    <span style={{ fontFamily:"'Space Mono', monospace", fontSize:12, color:s.color, fontWeight:700 }}>{s.value}%</span>
                  </div>
                  <div style={{ height:3, background:C.border, borderRadius:2 }}>
                    <div style={{ width:`${s.value}%`, height:"100%", background:s.color, borderRadius:2, transition:"width 1s" }}></div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop:12, padding:"8px 10px", background:C.bg, borderRadius:8, border:`1px dashed ${C.border}` }}>
              <div style={{ fontSize:9, color:C.muted, fontFamily:"'Space Mono', monospace", marginBottom:2 }}>CONTROVERSY INDEX</div>
              <div style={{ fontSize:11, color:C.text }}>36% negative is <span style={{ color:C.neg }}>3.3×</span> higher than a typical AFCON championship announcement</div>
            </div>
          </div>
        </div>

        {/* ── HASHTAGS + TWEET FEED ──────────────────────────────────────────── */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1.2fr", gap:12, marginBottom:18 }}>

          {/* Hashtags */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
            <div style={{ fontFamily:"'Syne', sans-serif", fontWeight:700, fontSize:14, marginBottom:2 }}>Top Hashtags</div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:14 }}>Volume in thousands · Ruling reaction hashtags dominate</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={HASHTAGS} layout="vertical">
                <XAxis type="number" tick={{ fontSize:9, fill:C.muted }} tickFormatter={v => `${v}K`} />
                <YAxis type="category" dataKey="tag" tick={{ fontSize:9, fill:C.text }} width={115} />
                <Tooltip contentStyle={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, fontSize:11 }} formatter={v => [`${v}K tweets`]} />
                <Bar dataKey="count" radius={[0, 5, 5, 0]}>
                  {HASHTAGS.map((entry, i) => (
                    <Cell key={i} fill={entry.tag.includes("Stolen") || entry.tag.includes("Senegal") || entry.tag.includes("CAS") ? C.neg : entry.tag.includes("Morocco") || entry.tag.includes("Atlas") ? C.pos : C.green} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display:"flex", gap:12, marginTop:8 }}>
              {[["Morocco support", C.pos], ["Ruling opposition", C.neg], ["CAF/Neutral", C.green]].map(([l,c]) => (
                <div key={l} style={{ display:"flex", alignItems:"center", gap:4 }}>
                  <div style={{ width:8, height:8, background:c, borderRadius:2 }}></div>
                  <span style={{ fontSize:9, color:C.muted }}>{l}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tweet Feed */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
              <div>
                <div style={{ fontFamily:"'Syne', sans-serif", fontWeight:700, fontSize:14 }}>Live Feed</div>
                <div style={{ fontSize:11, color:C.muted }}>Sorted by influence · {filtered.length} tweets</div>
              </div>
              <div style={{ display:"flex", gap:4 }}>
                {["all","positive","negative","neutral"].map(f => (
                  <button key={f} className="fbtn tabtn" onClick={() => setFilter(f)} style={{ padding:"3px 8px", borderRadius:6, fontSize:9, fontWeight:700, textTransform:"uppercase", letterSpacing:0.5, fontFamily:"'Space Mono', monospace", background:filter===f ? (f==="positive"?C.pos:f==="negative"?C.neg:f==="neutral"?C.neu:"#1a3020") : C.bg, color:C.text, borderColor:filter===f ? "transparent" : C.border, borderWidth:1, borderStyle:"solid" }}>
                    {f==="all"?"ALL":f.slice(0,3).toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ height:280, overflowY:"auto" }}>
              {filtered.map(t => {
                const badge = sentBadge(t.sentiment);
                return (
                  <div key={t.id} className="trow" style={{ background:"#0a190c", border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 12px", marginBottom:6 }}>
                    <div style={{ display:"flex", gap:8 }}>
                      <div style={{ fontSize:18, flexShrink:0 }}>{t.avatar}</div>
                      <div style={{ flex:1, minWidth:0 }}>
                        <div style={{ display:"flex", alignItems:"center", gap:6, flexWrap:"wrap", marginBottom:4 }}>
                          <span style={{ fontSize:12, fontWeight:700, color:C.text }}>{t.user}</span>
                          <span style={{ fontSize:9, color:C.muted }}>{t.handle}</span>
                          <span style={{ fontSize:9, color:C.muted }}>{t.country} · {t.time}</span>
                          <div style={{ marginLeft:"auto", background:badge.bg, color:badge.color, fontSize:8, fontWeight:700, padding:"2px 5px", borderRadius:4, fontFamily:"'Space Mono', monospace", border:`1px solid ${badge.border}` }}>{badge.label}</div>
                        </div>
                        <div style={{ fontSize:11, color:"#9ab89a", lineHeight:1.45 }}>{t.text.slice(0,120)}{t.text.length > 120 ? "…" : ""}</div>
                        <div style={{ display:"flex", gap:12, marginTop:6 }}>
                          <span style={{ fontSize:10, color:C.muted }}>❤️ {t.likes}</span>
                          <span style={{ fontSize:10, color:C.muted }}>🔁 {t.rt}</span>
                          <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:4 }}>
                            <div style={{ width:32, height:3, background:C.border, borderRadius:2 }}>
                              <div style={{ width:`${Math.round(Math.abs(t.score)*100)}%`, height:"100%", background:t.score > 0 ? C.pos : C.neg, borderRadius:2 }}></div>
                            </div>
                            <span style={{ fontSize:9, fontFamily:"'Space Mono', monospace", color:t.score > 0 ? C.pos : C.neg }}>{t.score > 0 ? "+" : ""}{t.score.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── AI ANALYZER ────────────────────────────────────────────────────── */}
        <div style={{ background:"linear-gradient(135deg, #080f09, #060810)", border:`1px solid #1a2a2a`, borderRadius:12, padding:20, marginBottom:18 }}>
          <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:16 }}>
            <div style={{ width:32, height:32, background:"linear-gradient(135deg, #7c3aed, #4f46e5)", borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 }}>✦</div>
            <div>
              <div style={{ fontFamily:"'Syne', sans-serif", fontWeight:800, fontSize:15 }}>Claude AI Analyzer</div>
              <div style={{ fontSize:11, color:C.muted }}>Paste any tweet — get real sentiment, emotions, and stance in seconds</div>
            </div>
            <div style={{ marginLeft:"auto", display:"flex", gap:6 }}>
              <span style={{ background:"#1a0a2a", border:"1px solid #3a1a5a", color:"#a78bfa", fontSize:9, padding:"3px 8px", borderRadius:6, fontFamily:"'Space Mono', monospace" }}>CLAUDE-SONNET-4</span>
            </div>
          </div>

          <div style={{ display:"flex", gap:8, marginBottom:16 }}>
            <input
              value={tweet}
              onChange={e => setTweet(e.target.value)}
              onKeyDown={e => e.key === "Enter" && analyze()}
              placeholder='Try: "Morocco deserved this, Senegal broke the rules" or paste a real tweet...'
              style={{ flex:1, background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"11px 14px", color:C.text, fontSize:12, fontFamily:"system-ui, sans-serif" }}
            />
            <button
              className="abtn"
              onClick={analyze}
              disabled={loading}
              style={{ background:loading ? C.muted : "linear-gradient(135deg, #7c3aed, #4f46e5)", color:"#fff", border:"none", borderRadius:8, padding:"11px 22px", fontSize:12, fontWeight:700, whiteSpace:"nowrap", opacity:loading ? 0.6 : 1 }}
            >
              {loading ? "⏳ Analyzing..." : "Analyze →"}
            </button>
          </div>

          {result && !result.error && (
            <div style={{ background:C.card, borderRadius:10, padding:16, border:`1px solid ${C.border}` }}>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:12, marginBottom:14 }}>
                {[
                  { label:"SENTIMENT", value:result.sentiment?.toUpperCase(), color:result.sentiment==="positive"?C.pos:result.sentiment==="negative"?C.neg:C.neu },
                  { label:"SCORE", value:(result.score >= 0 ? "+" : "") + result.score?.toFixed(2), color:C.gold },
                  { label:"CONFIDENCE", value:`${Math.round((result.confidence||0)*100)}%`, color:C.text },
                  { label:"STANCE", value:result.side?.replace("pro-",""), color:"#a78bfa" },
                ].map(item => (
                  <div key={item.label}>
                    <div style={{ fontSize:9, color:C.muted, fontFamily:"'Space Mono', monospace", marginBottom:4, letterSpacing:1 }}>{item.label}</div>
                    <div style={{ fontFamily:"'Syne', sans-serif", fontSize:20, fontWeight:800, color:item.color, textTransform:"uppercase" }}>{item.value}</div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize:12, color:"#9ab89a", lineHeight:1.5, marginBottom:12, padding:"8px 12px", background:C.bg, borderRadius:8, borderLeft:`3px solid #3a5a3a` }}>
                {result.summary}
              </div>

              {result.emotions && (
                <div style={{ marginBottom:12 }}>
                  <div style={{ fontSize:9, color:C.muted, fontFamily:"'Space Mono', monospace", letterSpacing:1, marginBottom:8 }}>EMOTION BREAKDOWN</div>
                  <div style={{ display:"flex", gap:12, flexWrap:"wrap" }}>
                    {Object.entries(result.emotions).map(([emotion, score]) => {
                      const pct = Math.round((score||0)*100);
                      return (
                        <div key={emotion} style={{ flex:1, minWidth:80 }}>
                          <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
                            <span style={{ fontSize:10, color:C.muted, textTransform:"capitalize" }}>{emotion}</span>
                            <span style={{ fontSize:10, fontFamily:"'Space Mono', monospace", color:pct > 50 ? C.neg : C.muted }}>{pct}%</span>
                          </div>
                          <div style={{ height:3, background:C.border, borderRadius:2 }}>
                            <div style={{ width:`${pct}%`, height:"100%", background:emotion==="joy"||emotion==="pride"?C.pos:emotion==="anger"||emotion==="frustration"?C.neg:C.neu, borderRadius:2, transition:"width 0.5s" }}></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {result.keywords && (
                <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                  {result.keywords.map(kw => (
                    <span key={kw} style={{ background:C.bg, border:`1px solid ${C.border}`, color:C.text, fontSize:10, padding:"3px 10px", borderRadius:20 }}>#{kw}</span>
                  ))}
                </div>
              )}
            </div>
          )}
          {result?.error && (
            <div style={{ color:C.neg, fontSize:12, padding:"8px 12px", background:"#1a0505", borderRadius:8, border:`1px solid #3a0505` }}>
              ⚠ Analysis failed. Ensure you're running this in Claude.ai with API access enabled.
            </div>
          )}
        </div>

        {/* ── FOOTER ─────────────────────────────────────────────────────────── */}
        <div style={{ textAlign:"center", padding:"14px 0 4px", borderTop:`1px solid ${C.border}` }}>
          <div style={{ fontFamily:"'Space Mono', monospace", fontSize:10, color:C.muted }}>
            // This app was built by CeeJay for Chinedum Aranotu – 2026
          </div>
          <div style={{ fontSize:10, color:"#2a4a2a", marginTop:4 }}>
            Data: Mock dataset reflecting real CAF ruling controversy · Claude Sonnet 4 · recharts
          </div>
        </div>

      </div>
    </div>
  );
}
