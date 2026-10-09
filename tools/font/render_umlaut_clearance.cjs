// Independent browser profile; CHROME_BIN may select an installed Chrome.
const {chromium}=require('playwright');
const fs=require('fs');const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../..');
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_BIN?{executablePath:process.env.CHROME_BIN}:{})});
 const page=await browser.newPage({viewport:{width:1120,height:800}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file://'+root+'/tools/font/umlaut-clearance-proof.html');
 await page.evaluate(async()=>{await document.fonts.load('32px QFW','ÜüÜü');await document.fonts.load('32px QFWTTF','ÜüÜü');await document.fonts.ready;});
 const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 const {root:doc}=await cdp.send('DOM.getDocument');
 const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:doc.nodeId,selector:'.sample'});
 for(const nodeId of nodeIds){const {fonts}=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});if(!fonts.length||fonts.some(f=>!f.isCustomFont||!f.familyName.includes('QuanFangwei')))throw Error('Fallback: '+JSON.stringify(fonts));}
 const widths=await page.evaluate(()=>{const c=document.createElement('canvas').getContext('2d'),out=[];for(const font of ['QFW','QFWTTF']){c.font='64px '+font;for(const [a,b] of [['Ü','Ü'],['ü','ü'],['U','Ü'],['u','ü']]){const x=c.measureText(a).width,y=c.measureText(b).width;if(Math.abs(x-y)>.01)throw Error('Width mismatch');out.push({font,base:a,marked:b,advance:x});}}return out;});
 await page.screenshot({path:root+'/tools/font/proofs/quanfangwei-umlaut-browser.png',fullPage:true});
 await page.pdf({path:root+'/tools/font/proofs/quanfangwei-umlaut-clearance.pdf',printBackground:true,preferCSSPageSize:true});
 if(errors.length)throw Error(JSON.stringify(errors));
 fs.writeFileSync(root+'/tools/font/reports/umlaut-browser.json',JSON.stringify({browser:await browser.version(),sampleNodes:nodeIds.length,allSampleFontsCustom:true,widths,errors},null,2)+'\n');
 await browser.close();console.log('PASS: umlaut browser samples use QFW; composed/decomposed advances match; PDF rendered');
})().catch(e=>{console.error(e);process.exit(1)});
