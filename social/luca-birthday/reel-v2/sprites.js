const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1600,height:1000}});
await p.goto('file://'+process.cwd()+'/sprites.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(1500);
for(const id of await p.$$eval('.s',e=>e.map(x=>x.id))) await p.locator('#'+id).screenshot({path:'sp/'+id+'.png',omitBackground:true});
await b.close()})()
