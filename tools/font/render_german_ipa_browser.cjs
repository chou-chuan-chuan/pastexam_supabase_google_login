// Optional proof rendering: npm install --no-save playwright; npx playwright install chromium
// CHROME_BIN can select an installed Chrome. Does not use a personal browser profile.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
 const root=path.resolve(__dirname, '../..');
 const out=path.join(root,'tools/font/proofs');
 const browser=await chromium.launch({...(process.env.CHROME_BIN ? {executablePath:process.env.CHROME_BIN} : {}),headless:true});
 const page=await browser.newPage({viewport:{width:1200,height:1100},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file://'+root+'/tools/font/german-ipa-proof.html');
 await page.evaluate(async()=>{await document.fonts.load('32px QFW','ɛɪɔʊʏøəɐɡʃʒŋʁʔˈˌːn̩i̯');await document.fonts.load('32px QFWTTF','n̩i̯');await document.fonts.ready;});
 const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 const {root:doc}=await cdp.send('DOM.getDocument');const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:doc.nodeId,selector:'.sample'});
 const fonts=[];for(const nodeId of nodeIds){const {fonts:f}=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});fonts.push(f);if(!f.length||f.some(x=>!x.isCustomFont||!x.familyName.includes('QuanFangwei')))throw Error('Fallback font detected: '+JSON.stringify(f));}
 const widths=await page.evaluate(()=>{const c=document.createElement('canvas').getContext('2d');let rows=[];for(const f of ['QFW','QFWTTF']){c.font='64px '+f;for(const [a,b] of [['n','n̩'],['l','l̩'],['m','m̩'],['i','i̯'],['ɐ','ɐ̯'],['aɪ','aɪ̯']]){const wa=c.measureText(a).width,wb=c.measureText(b).width;if(Math.abs(wa-wb)>.01)throw Error('advance mismatch');rows.push({font:f,base:a,marked:b,advance:wa});}}return rows;});
 await page.screenshot({path:out+'/quanfangwei-german-ipa-browser.png',fullPage:true});
 await page.pdf({path:out+'/quanfangwei-german-ipa.pdf',printBackground:true,preferCSSPageSize:true});
 fs.writeFileSync(root+'/tools/font/reports/german-ipa-browser.json',JSON.stringify({browser:await browser.version(),sampleNodes:fonts.length,allSampleFontsCustom:true,families:[...new Set(fonts.flat().map(x=>x.familyName))],widths,errors},null,2)+'\n');
 if(errors.length)throw Error(JSON.stringify(errors));
 console.log('PASS: '+fonts.length+' sample nodes use embedded QFW only; TTF/WOFF2 zero mark advances; PDF and screenshot saved');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
