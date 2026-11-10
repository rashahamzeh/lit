const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/layers.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(1500);
const ids=await p.$$eval('.L',e=>e.map(x=>x.id));
for(const id of ids){await p.locator('#'+id).screenshot({path:'L_'+id+'.png',omitBackground:id.startsWith('tx')});}
await b.close()})()
