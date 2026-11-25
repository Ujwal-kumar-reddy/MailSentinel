import React,{lazy,Suspense,useEffect,useState} from 'react'
import {createRoot} from 'react-dom/client'
import {Activity, BookOpen, ChartNoAxesColumn, Files, MailCheck, ScanLine, ShieldCheck} from 'lucide-react'
import Analyzer from './Analyzer'
import Batch from './Batch'
import {api} from './api'
import './style.css'
const Performance=lazy(()=>import('./Performance'))
const pages=[
 {id:'analyzer',name:'Email analyzer',icon:ScanLine,sub:'Inspect a message for spam using a trained email classifier.'},
 {id:'batch',name:'Batch analysis',icon:Files,sub:'Classify a collection of emails in one pass.'},
 {id:'performance',name:'Model performance',icon:ChartNoAxesColumn,sub:'Explore the validation benchmark and the selected model’s held-out results.'},
 {id:'technology',name:'About the technology',icon:BookOpen,sub:'Inside the MailSentinel classification pipeline.'}]
function About(){return <section className="paper prose"><h2>From inbox text to a probability</h2>
 <h3>Training data</h3><p>The Apache SpamAssassin public corpus contains labelled email, including legitimate newsletters that resemble spam. The loader reads the subject and MIME text body, then removes normalized duplicates before splitting the data. The training set also includes short, authored examples of everyday correspondence and spam.</p>
 <h3>Learning from words</h3><p>TF-IDF weights words and adjacent word pairs by their frequency within a message and their rarity across training emails. Four classifiers are compared on validation emails, with a higher cost for flagging legitimate mail.</p>
 <h3>Reading the score</h3><p>Sigmoid calibration maps model outputs to estimated probabilities using out-of-fold predictions. Each model uses a cutoff selected on validation emails to balance false alarms against missed spam. The training corpus is historical, so accuracy can change across languages, senders and newer campaigns.</p>
 <h3>Warning indicators</h3><p>Separate rules flag patterns such as urgency or credential requests. These indicators describe what matched in the text. They do not explain an individual model decision.</p>
 <a className="more" href="#performance">View evaluation results →</a></section>}
function App(){
 const route=()=>pages.find(p=>p.id===location.hash.slice(1))||pages[0]
 const [page,setPage]=useState(route),[status,setStatus]=useState('Checking API')
 useEffect(()=>{const update=()=>{setPage(route());window.scrollTo(0,0)};window.addEventListener('hashchange',update);return()=>window.removeEventListener('hashchange',update)},[])
 useEffect(()=>{let live=true;const check=()=>api<{status:string}>('/health').then(()=>{if(live)setStatus('API connected')}).catch(()=>{if(live)setStatus('API unavailable')});void check();const t=setInterval(check,120000);return()=>{live=false;clearInterval(t)}},[])
 useEffect(()=>{document.title=page.name+' · MailSentinel'},[page])
 return <><header><a className="brand" href="#analyzer"><ShieldCheck size={30}/>MailSentinel</a><span className="service"><Activity size={15}/>{status}</span></header><div className="shell"><nav aria-label="Workspace">{pages.map(p=><a key={p.id} href={'#'+p.id} aria-current={page.id===p.id?'page':undefined}><p.icon size={18}/>{p.name}</a>)}</nav>
 <main><div className="hero"><div><h1>{page.name}</h1><p>{page.sub}</p></div><div className="emblem" aria-hidden="true"><MailCheck size={60} strokeWidth={1}/></div></div>
 <Suspense fallback={<p>Loading dashboard…</p>}>{page.id==='analyzer'?<Analyzer/>:page.id==='batch'?<Batch/>:page.id==='performance'?<Performance/>:<About/>}</Suspense>
 <footer><ShieldCheck size={16}/>Spam predictions are probabilistic and cannot guarantee email safety.</footer></main></div></>}
createRoot(document.getElementById('root')!).render(<App/>)
