export type Email = {subject: string, body: string}
export type Prediction = {label: 'spam'|'legitimate', spam_probability: number, model: string, indicators: string[]}
export type Scores = {accuracy:number, precision:number, recall:number, f1:number, confusion:number[][], brier:number}
type Counts = {spam:number, legitimate:number}
export type Report = {winner:string, dataset:{raw:Counts,clean:Counts,duplicates:number,median_chars:number}, validation:Record<string,Scores>, test:Scores, splits:Record<string,Counts>}

const base = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
export async function api<T>(path:string, payload?: unknown): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 90000)
  try {
    const response = await fetch(base + path, {signal:controller.signal, cache:'no-store', ...(payload === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})})
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(typeof error.detail === 'string' ? error.detail : 'The service could not complete the request.')
    }
    return await response.json() as T
  } catch(error) {
    if(error instanceof TypeError) throw new Error('Cannot reach the prediction service. Check the API connection and retry.')
    if(controller.signal.aborted) throw new Error('The service timed out. Please retry.')
    throw error
  } finally { clearTimeout(timer) }
}
export const percent = (value:number) => (value*100).toFixed(1)+'%'
