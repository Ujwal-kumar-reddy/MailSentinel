import test from 'node:test'
import assert from 'node:assert/strict'
import {parseEmails,resultsCsv} from '../src/csv.js'
test('quoted multiline and escaping',()=>assert.deepEqual(parseEmails('\uFEFFbody,subject\r\n"two,\r\nlines","A ""quote"""'),[{subject:'A "quote"',body:'two,\nlines'}]))
test('reject malformed and oversized CSV',()=>{for(const s of ['x,y\na,b','body,subject\n"x,y','subject,body\nx','subject,body\n'+('a,b\n'.repeat(101))])assert.throws(()=>parseEmails(s))})
test('export maps records without repeating private input',()=>assert.equal(resultsCsv([{label:'spam',spam_probability:0.8}]),'record,label,spam_probability\r\n1,spam,0.8'))
