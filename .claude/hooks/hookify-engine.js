#!/usr/bin/env node

const fs=require("fs");
const path=require("path");

const PROJECT_DIR=process.env.CLAUDE_PROJECT_DIR||process.cwd();
const CLAUDE_DIR=path.join(PROJECT_DIR,".claude");
const DEBUG=process.env.HOOKIFY_DEBUG==="1";

function debug(...a){if(DEBUG)console.error("[hookify-engine]",...a)}

function parseFrontmatter(content){
  const LF=String.fromCharCode(10);
  const regex=new RegExp("^---"+LF+"([\\s\\S]*?)"+LF+"---"+LF+"([\\s\\S]*)$");
  const m=content.match(regex);
  if(!m)return null;
  const[,yaml,body]=m;
  const cfg={};
  yaml.split(LF).forEach(l=>{
    const i=l.indexOf(":");
    if(i===-1)return;
    const k=l.slice(0,i).trim();
    let v=l.slice(i+1).trim();
    if(v==="true")v=true;
    else if(v==="false")v=false;
    cfg[k]=v;
  });
  return{config:cfg,message:body.trim()};
}

function loadRules(){
  const rules=[];
  try{
    const files=fs.readdirSync(CLAUDE_DIR).filter(f=>f.startsWith("hookify.")&&f.endsWith(".md"));
    debug("Found:",files);
    for(const f of files){
      try{
        const c=fs.readFileSync(path.join(CLAUDE_DIR,f),"utf8");
        const p=parseFrontmatter(c);
        if(!p){debug("Skip "+f+": no frontmatter");continue}
        const{config:cfg,message:msg}=p;
        if(!cfg.name||!cfg.pattern||!cfg.action){debug("Skip "+f+": missing fields");continue}
        if(cfg.enabled===false){debug("Skip "+f+": disabled");continue}
        rules.push({name:cfg.name,pattern:cfg.pattern,action:cfg.action,event:cfg.event||"file",message:msg,file:f});
        debug("Loaded:",cfg.name);
      }catch(e){debug("Err "+f+":",e.message)}
    }
  }catch(e){debug("Err dir:",e.message)}
  return rules;
}

function matches(fp,pt){
  try{return new RegExp(pt).test(fp)}
  catch(e){debug("Bad regex:",pt);return false}
}

async function main(){
  let input="";
  try{input=fs.readFileSync(0,"utf8")}
  catch(e){debug("No stdin");process.exit(0)}
  if(!input.trim()){debug("Empty");process.exit(0)}
  let h;
  try{h=JSON.parse(input)}
  catch(e){debug("Bad JSON");process.exit(0)}
  debug("Data:",JSON.stringify(h,null,2));
  const t=h.tool_input||{};
  const fp=t.file_path||t.path||"";
  if(!fp){debug("No path");process.exit(0)}
  debug("Check:",fp);
  const rules=loadRules();
  if(!rules.length){debug("No rules");process.exit(0)}
  for(const r of rules){
    if(r.event!=="file")continue;
    if(matches(fp,r.pattern)){
      debug("MATCH:",r.name);
      if(r.action==="block"){console.log(r.message);process.exit(2)}
    }
  }
  debug("No match");
  process.exit(0);
}

main().catch(e=>{debug("Err:",e.message);process.exit(0)});