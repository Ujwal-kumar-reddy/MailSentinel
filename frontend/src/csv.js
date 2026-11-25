export function parseEmails(source) {
  const text = source.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n')
  const rows = []
  let row = [], cell = '', quoted = false, closed = false
  const endCell = () => {row.push(cell); cell = ''; closed = false}
  const endRow = () => { endCell(); if (row.some(value => value.trim())) rows.push(row); row = [] }
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (quoted) {
      if (ch !== '"') cell += ch
      else if (text[i+1] === '"') {cell += '"'; i++}
      else {quoted = false; closed = true}
    } else if (ch === ',') endCell()
    else if (ch === '\n') endRow()
    else if (ch === '"' && !cell && !closed) quoted = true
    else if (closed || ch === '"') throw Error('Malformed quotation mark in CSV.')
    else cell += ch
  }
  if (quoted) throw Error('Unclosed quoted field in CSV.')
  endRow()
  const header = rows.shift()?.map(h => h.trim().toLowerCase()) || []
  if (header.length !== 2 || !header.includes('subject') || !header.includes('body')) throw Error('Use exactly two column headers: subject and body.')
  if (!rows.length || rows.length > 100) throw Error('Upload between 1 and 100 email rows.')
  return rows.map((fields, i) => {
    const subject = fields[header.indexOf('subject')] || '', body = fields[header.indexOf('body')] || ''
    if (fields.length !== 2 || subject.length > 500 || body.length > 50000 || !(subject+body).trim()) throw Error('Check fields and length in record '+(i+1)+'.')
    return {subject,body}
  })
}

export function resultsCsv(results) {
  return ['record,label,spam_probability', ...results.map((r,i) => [i+1,r.label,r.spam_probability].join(','))].join('\r\n')
}
