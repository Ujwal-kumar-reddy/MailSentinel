import {useEffect,useState} from 'react'
import {BarChart,Bar,ResponsiveContainer,XAxis,YAxis,Tooltip,CartesianGrid} from 'recharts'
import {api,percent,type Report} from './api'
const metrics=['accuracy','precision','recall','f1'] as const
export default function Performance(){
 const [data,setData]=useState<Report|null>(null),[error,setError]=useState(''),[attempt,retry]=useState(0),[selected,select]=useState('test')
 useEffect(()=>{let active=true;setError('');api<Report>('/metrics').then(v=>{if(active)setData(v)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[attempt])
 if(!data)return <section className="paper" role="status">{error?<>{error} <button className="plain" onClick={()=>retry(attempt+1)}>Retry</button></>:'Loading evaluation results…'}</section>
 const matrix=(selected==='test'?data.test:data.validation[selected]).confusion
 const counts=data.dataset.clean
 return <div className="stack"><section className="paper"><h2>Held-out test · {data.winner}</h2><div className="stats">{metrics.map(m=><div key={m}><small>{m.toUpperCase()}</small><strong>{percent(data.test[m])}</strong></div>)}</div></section>
 <section className="paper"><h2>Validation comparison</h2><p>Bars show archive validation spam F1. Model selection also considers false positives and short emails.</p><div className="chart"><ResponsiveContainer width="100%" height={220}><BarChart layout="vertical" data={Object.entries(data.validation).sort((a,b)=>b[1].f1-a[1].f1).map(([name,s])=>({name,F1:+(100*s.f1).toFixed(2)}))}><CartesianGrid horizontal={false} stroke="#d9ded6"/><XAxis type="number" domain={[0,100]} unit="%"/><YAxis type="category" dataKey="name" width={125} tick={{fontSize:11}}/><Tooltip/><Bar dataKey="F1" fill="#235341" barSize={18}/></BarChart></ResponsiveContainer></div>
 <div className="scroll"><table><thead><tr><th>Model</th>{metrics.map(m=><th key={m}>{m}</th>)}</tr></thead><tbody>{Object.entries(data.validation).map(([name,s])=><tr key={name}><td>{name}</td>{metrics.map(m=><td key={m}>{percent(s[m])}</td>)}</tr>)}</tbody></table></div></section>
 <div className="columns even"><section className="paper"><h2>Confusion matrix</h2><label htmlFor="split">Evaluation set</label><select id="split" value={selected} onChange={e=>select(e.target.value)}><option value="test">Test · {data.winner}</option>{Object.keys(data.validation).map(s=><option key={s} value={s}>Validation · {s}</option>)}</select><table><thead><tr><th>Actual ↓ / Predicted →</th><th>Legitimate</th><th>Spam</th></tr></thead><tbody>{matrix.map((row,i)=><tr key={i}><th>{i?'Spam':'Legitimate'}</th>{row.map((n,j)=><td key={j} className={i===j?'correct':''}>{n}</td>)}</tr>)}</tbody></table></section>
 <section className="paper"><h2>Dataset distribution</h2><p>After cleaning and duplicate removal</p><div className="dist"><i style={{width:100*counts.legitimate/(counts.spam+counts.legitimate)+'%'}}/></div><p>Legitimate · {counts.legitimate.toLocaleString()}<br/>Spam · {counts.spam.toLocaleString()}</p><p>{data.dataset.duplicates} repeated records detected.</p></section></div></div>
}
