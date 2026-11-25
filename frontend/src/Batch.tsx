import {useState} from 'react'
import {Download, Files, Upload} from 'lucide-react'
import {api,percent,type Email,type Prediction} from './api'
import {parseEmails,resultsCsv} from './csv'

function download(text:string,name:string){
  const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}))
  const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
export default function Batch(){
  const [emails,setEmails]=useState<Email[]>([]),[results,setResults]=useState<Prediction[]>([])
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[name,setName]=useState('')
  async function read(file?:File){setEmails([]);setResults([]);setError('');setName(file?.name||'')
    if(!file)return
    setBusy(true)
    try{if(file.size>2000000)throw Error('Choose a CSV under 2 MB.');setEmails(parseEmails(await file.text()))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  async function run(){setBusy(true);setError('')
    try{setResults((await api<{results:Prediction[]}>('/predict-batch',{emails})).results)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  return <section className="paper"><div className="sectionTitle"><Files/><h2>Import emails</h2></div><p>Upload a UTF-8 CSV with subject and body columns. Include up to 100 records per batch.</p>
    <label className="upload"><Upload/><strong>{name||'Choose a CSV file'}</strong><input type="file" accept=".csv,text/csv" disabled={busy} onChange={e=>void read(e.target.files?.[0])}/></label>
    <div className="actions"><button className="primary" disabled={!emails.length||busy} onClick={run}>{busy?'Processing…':'Analyze batch'}{emails.length?' · '+emails.length:''}</button><button className="plain" onClick={()=>download('subject,body\r\nMeeting notes,Can you review the agenda for Friday?','template.csv')}>Download template</button></div>
    {error&&<p role="alert" className="error">{error}</p>}{results.length>0&&<><div className="sectionTitle mt-8"><h2>Classification results</h2><button className="plain" onClick={()=>download(resultsCsv(results),'mailsentinel-results.csv')}><Download size={15}/> Export CSV</button></div>
    <div className="scroll"><table><thead><tr><th>Record</th><th>Subject</th><th>Classification</th><th>Spam probability</th></tr></thead><tbody>{results.map((r,i)=><tr key={i}><td>{i+1}</td><td>{emails[i].subject||'—'}</td><td>{r.label}</td><td>{percent(r.spam_probability)}</td></tr>)}</tbody></table></div></>}</section>
}
