import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import http from 'node:http';
export default async function setup() {
  const directory = mkdtempSync(path.join(tmpdir(), 'modelforge-browser-'));
  const host = '127.0.0.2';
  process.env.MODELFORGE_TEST_API = `http://${host}:8003`;
  const root = path.resolve('..');
  const server = spawn(path.join(root,'backend/.venv/bin/python'), ['-m','uvicorn','app.main:app','--app-dir',path.join(root,'backend'),'--host',host,'--port','8003'], { env: { ...process.env, MODELFORGE_DATA_DIR: path.join(directory,'data'), OLLAMA_BASE_URL:'http://127.0.0.1:1', OMP_NUM_THREADS:'1', OPENBLAS_NUM_THREADS:'1' }, stdio:'ignore' });
  let ready=false;
  for(let i=0;i<100;i++) {
    if(server.exitCode !== null) throw new Error('Isolated backend exited before startup.');
    ready=await new Promise<boolean>(resolve=>{
      const request=http.get({host,port:8003,path:'/api/v1/health'},response=>{response.resume();resolve(response.statusCode===200);});
      request.on('error',()=>resolve(false));
    });
    if(ready) break;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  if(!ready) {server.kill();throw new Error('Isolated backend did not become ready.');}
  return async()=>{
    server.kill('SIGTERM');
    await new Promise<void>(resolve=>server.once('exit',()=>resolve()));
    rmSync(directory,{recursive:true,force:true});
  };
}
