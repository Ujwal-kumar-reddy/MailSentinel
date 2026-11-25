import {useState} from 'react'
import {ArrowUpRight, ChevronRight, Fingerprint, Inbox, LockKeyhole, Mail, ScanLine, TriangleAlert} from 'lucide-react'
import {api, percent, type Email, type Prediction} from './api'

const samples = [
  {name:'Prize notification',subject:'Congratulations! Claim your prize today',body:'You have won a cash prize in our lottery. Act now to claim your prize and receive your free reward. Visit https://example.invalid/prize before the offer expires.'},
  {name:'Project update',subject:'Notes from the project review',body:'Hi Priya,\n\nThanks for reviewing the prototype this morning. I added the accessibility feedback to our meeting notes. Can we walk through the revised screens on Thursday?\n\nThanks,\nSam'},
]
export default function Analyzer(){
  const [mail,setMail] = useState<Email>({subject:'',body:''})
  const [result,setResult] = useState<Prediction|null>(null)
  const [busy,setBusy] = useState(false), [error,setError] = useState('')
  function edit(next:Email){setMail(next);setResult(null);setError('')}
  async function analyze(){setBusy(true);setError('');setResult(null)
    try{setResult(await api<Prediction>('/predict',mail))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  return <div className="columns"><section className="paper"><div className="sectionTitle"><Mail/><h2>Email content</h2></div>
    <form onSubmit={e=>{e.preventDefault();void analyze()}}><fieldset disabled={busy}>
    <label htmlFor="subject">Subject</label><input id="subject" value={mail.subject} maxLength={500} onChange={e=>edit({...mail,subject:e.target.value})} placeholder="Enter the subject line"/>
    <label htmlFor="body">Message body</label><textarea id="body" rows={8} value={mail.body} maxLength={50000} onChange={e=>edit({...mail,body:e.target.value})} placeholder="Paste the email text here…"/>
    <div className="counter">{mail.body.length.toLocaleString()} / 50,000</div>
    <div className="examples"><span>Try an example</span>{samples.map(s=><button type="button" key={s.name} onClick={()=>edit({subject:s.subject,body:s.body})}>{s.name}<ArrowUpRight size={13}/></button>)}</div>
    <div className="actions"><button className="primary" disabled={busy||!(mail.subject+mail.body).trim()}><ScanLine size={18}/>{busy?'Analyzing…':'Analyze email'}</button><button className="plain" type="button" onClick={()=>edit({subject:'',body:''})}>Clear</button></div>
    </fieldset></form>{error&&<p className="error" role="alert">{error}</p>}</section>
    <aside><section className="result" aria-live="polite"><div className="sectionTitle"><Fingerprint/><h2>Analysis result</h2></div>
    {result?<><div className={'verdict '+result.label}>{result.label}</div><p>{result.model}</p><div className="reading"><span>Spam probability</span><b>{percent(result.spam_probability)}</b></div><progress max={1} value={result.spam_probability}/>
    <h3>Heuristic indicators</h3>{result.indicators.length?<ul>{result.indicators.map(i=><li key={i}><TriangleAlert size={14}/> {i}</li>)}</ul>:<p>No configured indicators matched.</p>}<small>These text matches are independent of the model score.</small></>:<div className="waiting"><Inbox size={38} strokeWidth={1.25}/><h3>{busy?'Analyzing email…':'Awaiting an email'}</h3><p>Your classification and spam probability will appear here.</p></div>}</section>
    <div className="privacy"><LockKeyhole/><div><h3>Private by design</h3><p>Submitted text is processed in memory. Links and attachments are never opened.</p></div></div>
    <a className="more" href="#technology">How the classifier works <ChevronRight size={15}/></a></aside></div>
}
