// Independent browser profile; CHROME_BIN may select an installed Chrome.
const {chromium}=require('playwright');
const fs=require('fs');const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../..');
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_BIN?{executablePath:process.env.CHROME_BIN}:{})});
 const page=await browser.newPage({viewport:{width:1120,height:800}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file://'+root+'/tools/font/turned-a-proof.html');
 await page.evaluate(async()=>{await document.fonts.load('32px QFW','ɐ̯ e ə');await document.fonts.load('32px QFWTTF','ɐ̯ e ə');await document.fonts.ready;});
 const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 const {root:doc}=await cdp.send('DOM.getDocument');
 const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:doc.nodeId,selector:'.sample'});
 for(const nodeId of nodeIds){const {fonts}=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});if(!fonts.length||fonts.some(f=>!f.isCustomFont||!f.familyName.includes('QuanFangwei')))throw Error('Fallback: '+JSON.stringify(fonts));}
 const widths=await page.evaluate(()=>{const c=document.createElement('canvas').getContext('2d'),out=[];for(const text of ['e ə ɐ a','ˈmʏtɐ ˈzɔmɐ ˈbɛsɐ','ɐ̯ i̯ aɪ̯ n̩ l̩ m̩','Ü Ü ü ü']){c.font='64px QFW';const woff2=c.measureText(text).width;c.font='64px QFWTTF';const ttf=c.measureText(text).width;if(Math.abs(woff2-ttf)>.01)throw Error('TTF/WOFF2 width mismatch');out.push({text,woff2,ttf});}return out;});
 await page.screenshot({path:root+'/tools/font/proofs/quanfangwei-turned-a-browser.png',fullPage:true});
 await page.pdf({path:root+'/tools/font/proofs/quanfangwei-turned-a.pdf',printBackground:true,preferCSSPageSize:true});
 if(errors.length)throw Error(JSON.stringify(errors));
 fs.writeFileSync(root+'/tools/font/reports/turned-a-browser.json',JSON.stringify({browser:await browser.version(),sampleNodes:nodeIds.length,allSampleFontsCustom:true,widths,errors},null,2)+'\n');
 await browser.close();console.log('PASS: turned-a browser samples use QFW; two font formats loaded; text advances match; PDF rendered');
})().catch(e=>{console.error(e);process.exit(1)});
