/* Tiny local development server. Play the standalone HTML for offline use. */
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),portFlag=process.argv.indexOf('--port'),port=Number(process.env.PORT||(portFlag>=0?process.argv[portFlag+1]:8080));
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8'};
const server=http.createServer((req,res)=>{
  let pathname;try{pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);res.end('Bad path');return;}
  const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403);res.end('Forbidden');return;}
  fs.readFile(file,(err,content)=>{if(err){res.writeHead(404);res.end('Not found');return;}res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(content);});
});
server.listen(port,'0.0.0.0',()=>console.log(`Court Kings '26: http://localhost:${port}`));
