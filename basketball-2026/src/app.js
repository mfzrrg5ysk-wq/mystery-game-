(function(){
  'use strict';
  const {Game,STARS,clamp}=Court26, {Renderer,person}=CourtRender;
  const $=id=>document.getElementById(id);
  const game=new Game({idle:true,court:'arena',seed:Date.now()});
  const renderer=new Renderer($('court'));
  let mode='solo', playing=false, cup=null, lastState='idle', frameTime=0, accumulator=0, sound=false, audio=null;
  let record={wins:0,losses:0};try{record={...record,...JSON.parse(localStorage.getItem('court-kings-26-record')||'{}')};}catch{}
  const held=new Set(), pulses=[{},{}], touches=new Set(), tapTimes={};
  const options=()=>({mode,duration:Number($('duration').value),difficulty:$('difficulty').value,star0:$('star-home').value,star1:$('star-away').value,court:$('court-style').value});
  const pulse=(side,key)=>pulses[side][key]=true;
  function clearControls(){held.clear();touches.clear();pulses[0]={};pulses[1]={};for(const p of game.players)p.charge=null;}
  function beep(freq=500,duration=.07,shape='sine',volume=.06,delay=0){
    if(!sound||!audio)return;
    try{const o=audio.createOscillator(),g=audio.createGain(),time=audio.currentTime+delay;o.type=shape;o.frequency.setValueAtTime(freq,time);o.frequency.exponentialRampToValueAtTime(Math.max(70,freq*.6),time+duration);g.gain.setValueAtTime(volume,time);g.gain.exponentialRampToValueAtTime(.001,time+duration);o.connect(g);g.connect(audio.destination);o.start(time);o.stop(time+duration);}catch{}
  }
  function audioEvent(e){
    if(e.type==='score'){beep(660,.16,'sine',.07);beep(880,.19,'sine',.06,.10);beep(1320,.2,'sine',.05,.2);}
    else if(e.type==='green'){beep(880,.11,'sine',.05);beep(1174,.13,'sine',.05,.08);}
    else if(e.type==='rim')beep(250,.08,'triangle',.05);
    else if(e.type==='block'||e.type==='steal')beep(170,.16,'sawtooth',.035);
    else if(e.type==='whistle')beep(1700,.09,'sine',.025);
    else if(e.type==='super'){beep(400,.25,'sawtooth',.03);beep(800,.2,'sine',.05,.12);}
    else if(e.type==='buzzer')beep(110,.55,'sawtooth',.045);
    else if(e.type==='dash')beep(270,.09,'triangle',.03);
    else if(e.type==='shoot'||e.type==='catch')beep(160,.045,'triangle',.02);
  }
  function portrait(canvas,star,side){
    const c=canvas.getContext('2d');c.clearRect(0,0,canvas.width,canvas.height);
    const g=c.createRadialGradient(75,74,1,75,74,67);g.addColorStop(0,star.color+'35');g.addColorStop(1,star.color+'00');c.fillStyle=g;c.fillRect(0,0,150,160);
    person(c,{star,x:75,y:165,facing:side===0?1:-1,charge:null,vx:0},0,{scale:.95,portrait:true});
  }
  function renderRatings(){
    const star=STARS.find(s=>s.id===$('star-home').value);
    $('player-ratings').innerHTML=[['SHOT',star.shoot],['SPEED',star.speed],['DEFENSE',star.defense],['POWER',star.power]].map(([label,n])=>`<div class="rating-row"><span>${label}</span><div class="rating-track"><i style="width:${n}%"></i></div><strong>${n}</strong></div>`).join('');
    for(const card of document.querySelectorAll('.star-card')){const selected=card.dataset.star===star.id;card.classList.toggle('selected',selected);card.setAttribute('aria-pressed',String(selected));}
  }
  function setupPreview(){
    const a=STARS.find(s=>s.id===$('star-home').value),b=STARS.find(s=>s.id===$('star-away').value);
    portrait($('portrait-home'),a,0);portrait($('portrait-away'),b,1);$('role-home').textContent=a.role;$('role-away').textContent=b.role;renderRatings();
    if(!playing){game.start(options());game.state='idle';game.players[0].x=650;game.players[1].x=870;game.followBall();game.events=[];}
    $('menu-duration').textContent=mode==='practice'?'NO TIMER':`${$('duration').value} SECONDS`;
    $('start-btn').innerHTML=(mode==='versus'?'PLAY 2 PLAYER':mode==='tournament'?'ENTER THE CUP':mode==='practice'?'HIT THE COURT':'PLAY SOLO')+' <span aria-hidden="true">▶</span>';
    updateHud();
  }
  function chooseMode(next){
    if(playing)return;mode=next;
    for(const button of document.querySelectorAll('[data-mode]')){button.classList.toggle('selected',button.dataset.mode===mode);button.setAttribute('aria-pressed',String(button.dataset.mode===mode));}
    $('two-player-help').hidden=mode!=='versus';$('opponent-caption').textContent=mode==='versus'?'PLAYER 2':mode==='practice'?'PRACTICE':'CPU';
    document.querySelector('.control-strip').hidden=mode==='versus';
    $('court').setAttribute('aria-label',mode==='versus'?'Basketball court. Player 1: A and D move, W jump, hold B and release to shoot, S block, V super. Player 2: arrow keys move and jump, hold L and release to shoot, down arrow block, K super.':'Basketball court. Move with A and D, jump W, hold X then release to shoot, S to pump fake or block, Z for super shot.');
    $('star-away').disabled=mode==='practice';$('difficulty').disabled=mode==='versus'||mode==='practice';$('duration').disabled=mode==='practice';
    $('cup-panel').hidden=mode!=='tournament';if(mode==='tournament')$('cup-panel').innerHTML='<strong>8-PLAYER KNOCKOUT</strong>Three wins to take the title.';
    setupPreview();
  }
  function lockSetup(lock){
    for(const el of document.querySelectorAll('.setup select,.mode-tabs button,.star-card'))el.disabled=lock;
    if(!lock){$('star-away').disabled=mode==='practice';$('difficulty').disabled=mode==='versus'||mode==='practice';$('duration').disabled=mode==='practice';}
  }
  function newCup(){
    const o=options(),others=STARS.filter(s=>s.id!==o.star0&&s.id!==o.star1).map(s=>s.id);
    for(let i=others.length-1;i>0;i--){const j=Math.floor(game.random()*(i+1));[others[i],others[j]]=[others[j],others[i]];}
    const firstOpp=o.star1===o.star0?others.pop():o.star1;
    cup={round:0,entries:[o.star0,firstOpp,...others.slice(0,6)],completed:false};
  }
  function renderCup(){
    if(!cup){return;}
    const name=id=>(STARS.find(s=>s.id===id)||STARS[0]).short;
    $('cup-panel').hidden=false;
    let html=`<strong>${['QUARTERFINALS','SEMIFINALS','FINAL'][cup.round]}</strong>`;
    for(let i=0;i<cup.entries.length;i+=2)html+=`<div class="${i===0?'cup-active':''}"><span>${name(cup.entries[i])}</span><span>vs</span><span>${name(cup.entries[i+1])}</span></div>`;
    $('cup-panel').innerHTML=html;
  }
  function start(continuing=false){
    clearControls();if(mode==='tournament'&&!continuing)newCup();
    const o=options();if(mode==='tournament'){o.star1=cup.entries[1];$('star-away').value=o.star1;renderCup();portrait($('portrait-away'),STARS.find(s=>s.id===o.star1),1);$('role-away').textContent=STARS.find(s=>s.id===o.star1).role;}
    game.start(o);playing=true;lastState='countdown';lockSetup(true);document.body.classList.add('in-match');document.body.classList.remove('in-result');
    $('menu-overlay').hidden=true;$('result-overlay').hidden=true;$('pause-overlay').hidden=true;$('pause-btn').disabled=false;$('pause-btn').innerHTML='PAUSE <kbd>P</kbd>';
    $('round-label').textContent=mode==='tournament'?['QUARTERFINAL','SEMIFINAL','CHAMPIONSHIP'][cup.round]:mode==='practice'?'SHOOTAROUND':mode==='versus'?'LOCAL 2 PLAYER':'SOLO MATCH';
    $('court').focus({preventScroll:true});if(audio&&sound)audio.resume().catch(()=>{});$('announcement').textContent='Match started.';updateHud();
  }
  function menu(){
    playing=false;clearControls();game.state='idle';cup=null;lockSetup(false);document.body.classList.remove('in-match','in-result');
    $('menu-overlay').hidden=false;$('pause-overlay').hidden=true;$('result-overlay').hidden=true;$('pause-btn').disabled=true;$('pause-btn').innerHTML='PAUSE <kbd>P</kbd>';$('round-label').textContent='2026 EDITION';
    if(mode==='tournament')$('cup-panel').innerHTML='<strong>8-PLAYER KNOCKOUT</strong>Three wins to take the title.';
    setupPreview();
  }
  function togglePause(){if(!playing||game.state==='ended')return;clearControls();game.pause();$('pause-overlay').hidden=game.state!=='paused';$('pause-btn').innerHTML=game.state==='paused'?'RESUME <kbd>P</kbd>':'PAUSE <kbd>P</kbd>';(game.state==='paused'?$('resume-btn'):$('court')).focus({preventScroll:true});}
  function endMatch(){
    const won=game.winner===0;
    document.body.classList.add('in-result');
    $('result-overlay').hidden=false;clearControls();
    $('result-kicker').textContent=game.overtime?'OVERTIME FINAL':'FINAL SCORE';
    $('result-title').textContent=mode==='versus'?`PLAYER ${game.winner+1} WINS`:won?'YOU WIN':'TOUGH LOSS';
    $('result-score').innerHTML=`${game.players[0].score} <span>—</span> ${game.players[1].score}`;
    const s=game.players[0].stats;
    $('match-stats').innerHTML=[['BUCKETS',`${s.made}/${s.attempts}`],['THREES',s.threes],['STEALS',s.steals],['BLOCKS',s.blocks]].map(([label,value])=>`<div><strong>${value}</strong><span>${label}</span></div>`).join('');
    $('result-note').textContent=mode==='versus'?'Same keyboard. Settle the rematch.':won?'Good timing. Better defense.':'Get closer on defense. Find an open release.';
    $('rematch-btn').textContent='RUN IT BACK';$('rematch-btn').dataset.next='rematch';
    if(mode==='tournament'){
      if(won&&cup.round<2){
        const winners=[cup.entries[0]];for(let i=2;i<cup.entries.length;i+=2)winners.push(cup.entries[i+(game.random()<.5?0:1)]);
        cup.nextEntries=winners;$('rematch-btn').textContent=cup.round===0?'PLAY THE SEMIFINAL':'PLAY THE FINAL';$('rematch-btn').dataset.next='advance';
        $('result-note').textContent='You advance. The next round is waiting.';
      }else if(won){cup.completed=true;$('result-title').textContent='CUP CHAMPION';$('result-note').textContent='Three rounds. Three wins. Your court.';$('rematch-btn').textContent='NEW CUP';}
      else{$('result-title').textContent='CUP RUN ENDED';$('result-note').textContent='Knocked out. Start a new bracket to try again.';$('rematch-btn').textContent='TRY A NEW CUP';}
    }
    if(mode!=='versus'){
      record[won?'wins':'losses']++;try{localStorage.setItem('court-kings-26-record',JSON.stringify(record));}catch{}renderRecord();
    }
    $('announcement').textContent=`${$('result-title').textContent}. ${game.players[0].score} to ${game.players[1].score}.`;
    $('rematch-btn').focus({preventScroll:true});
  }
  function renderRecord(){$('record').textContent=`LOCAL RECORD ${record.wins} W / ${record.losses} L`;}
  function updateHud(){
    const [a,b]=game.players;
    $('home-label').textContent=a.star.name.toUpperCase();$('away-label').textContent=mode==='practice'?'SHOOTAROUND':b.star.name.toUpperCase();
    $('score-home').textContent=String(a.score).padStart(2,'0');$('score-away').textContent=String(b.score).padStart(2,'0');
    for(const [id,p] of [['home',a],['away',b]]){$(`heat-${id}`).style.width=p.heat+'%';$(`heat-${id}`).parentElement.classList.toggle('ready',p.heat>=99.9);}
    const seconds=Math.ceil(game.remaining);$('clock').textContent=mode==='practice'?'∞':game.overtime?'OT':`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
    $('clock-caption').textContent=!playing?'TIP-OFF':mode==='practice'?'PRACTICE':game.overtime?'NEXT BASKET WINS':game.state==='ended'?'FINAL':'GAME CLOCK';
    $('clock').parentElement.classList.toggle('low',playing&&!game.overtime&&game.remaining<10&&mode!=='practice');
    $('shot-clock').textContent=mode==='practice'?'NO SHOT CLOCK':game.ball.owner===null?'BALL IN THE AIR':`${Math.ceil(game.shotClock)} SECOND SHOT CLOCK`;
    $('possession-label').textContent=!playing?'READY WHEN YOU ARE':game.state==='ended'?'FINAL SCORE':game.state==='paused'?'TIMEOUT':game.ball.owner===null?'GET THE REBOUND':game.ball.owner===0?(a.heat>=100?'YOUR BALL · SUPER READY':'YOUR BALL'):(mode==='versus'?'PLAYER 2 BALL':'CPU BALL');
    $('stamina-label').textContent=`DASH STAMINA ${Math.round(a.stamina)}%`;
  }
  function inputFor(side){
    const versus=mode==='versus',out={...pulses[side]};pulses[side]={};
    if(side===0){out.move=(held.has('KeyD')||(!versus&&held.has('ArrowRight'))||touches.has('right')?1:0)-(held.has('KeyA')||(!versus&&held.has('ArrowLeft'))||touches.has('left')?1:0);}
    else out.move=(held.has('ArrowRight')?1:0)-(held.has('ArrowLeft')?1:0);
    return out;
  }
  const controls=new Set(['KeyA','KeyD','KeyW','KeyS','KeyX','KeyZ','KeyB','KeyV','KeyL','KeyK','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','ShiftLeft','ShiftRight','Space','KeyP','Escape']);
  function mapped(code){
    if(mode==='versus'){
      if(['KeyA','KeyD','KeyW','KeyS','KeyB','KeyV','ShiftLeft'].includes(code))return{side:0,action:({KeyW:'jump',KeyS:'defend',KeyB:'action',KeyV:'super',ShiftLeft:'dash'})[code]};
      return{side:1,action:({ArrowUp:'jump',ArrowDown:'defend',KeyL:'action',KeyK:'super',ShiftRight:'dash'})[code]};
    }
    return{side:0,action:({KeyW:'jump',ArrowUp:'jump',Space:'jump',KeyS:'defend',ArrowDown:'defend',KeyX:'action',KeyB:'action',KeyL:'action',KeyZ:'super',KeyV:'super',KeyK:'super',ShiftLeft:'dash',ShiftRight:'dash'})[code]};
  }
  document.addEventListener('keydown',e=>{
    if(!playing||!controls.has(e.code)||['SELECT','INPUT','TEXTAREA'].includes(e.target.tagName))return;
    e.preventDefault();if(e.repeat)return;
    if(e.code==='KeyP'||e.code==='Escape'){togglePause();return;}
    if(game.state==='paused'||game.state==='ended')return;
    held.add(e.code);const m=mapped(e.code);if(m.action)pulse(m.side,m.action);
    if(['KeyA','KeyD','ArrowLeft','ArrowRight'].includes(e.code)){
      const now=performance.now();if(now-(tapTimes[e.code]||-9999)<260)pulse(m.side,'dash');tapTimes[e.code]=now;
    }
  });
  document.addEventListener('keyup',e=>{held.delete(e.code);if(playing){const m=mapped(e.code);if(m.action==='action')pulse(m.side,'release');}});
  for(const button of document.querySelectorAll('[data-touch]')){
    const name=button.dataset.touch;
    button.addEventListener('pointerdown',e=>{e.preventDefault();if(!playing||game.state!=='playing')return;button.setPointerCapture(e.pointerId);touches.add(name);if(!['left','right'].includes(name))pulse(0,name);});
    const release=e=>{e.preventDefault();touches.delete(name);if(name==='action')pulse(0,'release');};
    button.addEventListener('pointerup',release);button.addEventListener('pointercancel',release);button.addEventListener('lostpointercapture',release);
  }
  window.addEventListener('blur',()=>{clearControls();if(playing&&!['ended','paused'].includes(game.state))togglePause();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){clearControls();if(playing&&!['ended','paused'].includes(game.state))togglePause();}});
  $('start-btn').addEventListener('click',()=>start());$('pause-btn').addEventListener('click',togglePause);$('resume-btn').addEventListener('click',togglePause);
  $('pause-menu-btn').addEventListener('click',menu);$('result-menu-btn').addEventListener('click',menu);
  $('rematch-btn').addEventListener('click',()=>{if($('rematch-btn').dataset.next==='advance'){cup.round++;cup.entries=cup.nextEntries;delete cup.nextEntries;start(true);}else start();});
  document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();if(playing&&game.state!=='ended'){if(game.state!=='paused')togglePause();}else menu();});
  $('sound-btn').addEventListener('click',()=>{
    sound=!sound;try{if(!audio){const Audio=window.AudioContext||window.webkitAudioContext;if(Audio)audio=new Audio();else sound=false;}if(audio&&sound)audio.resume().catch(()=>{});}catch{sound=false;}
    $('sound-btn').textContent=sound?'SOUND ON':'SOUND OFF';$('sound-btn').setAttribute('aria-pressed',String(sound));$('sound-btn').setAttribute('aria-label',sound?'Turn sound off':'Turn sound on');if(sound)beep(660,.1);
  });
  $('fullscreen-btn').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else if(document.querySelector('.arena-shell').requestFullscreen)await document.querySelector('.arena-shell').requestFullscreen();else $('announcement').textContent='Fullscreen is not available in this browser.';}catch{$('announcement').textContent='Fullscreen is not available in this browser.';}});
  document.addEventListener('fullscreenchange',()=>{$('fullscreen-btn').textContent=document.fullscreenElement?'EXIT FULLSCREEN':'FULLSCREEN';});
  for(const select of [$('star-home'),$('star-away')])select.innerHTML=STARS.map(s=>`<option value="${s.id}">${s.short}</option>`).join('');
  $('star-home').value='curry';$('star-away').value='wemby';
  for(const select of document.querySelectorAll('.setup select'))select.addEventListener('change',setupPreview);
  for(const button of document.querySelectorAll('[data-mode]'))button.addEventListener('click',()=>chooseMode(button.dataset.mode));
  $('roster').innerHTML=STARS.map(s=>`<button class="star-card" data-star="${s.id}" aria-pressed="false" aria-label="Select ${s.name}" style="--star-color:${s.color};--star-accent:${s.accent}"><span class="jersey">${s.num}</span><span><strong>${s.name}</strong><small>${s.special}</small></span></button>`).join('');
  for(const button of document.querySelectorAll('[data-star]'))button.addEventListener('click',()=>{if(!playing){$('star-home').value=button.dataset.star;setupPreview();}});
  function frame(now){
    const delta=Math.min((now-(frameTime||now))/1000,.1);frameTime=now;accumulator+=delta;
    let steps=0;
    while(accumulator>=1/120&&steps<12){game.update(1/120,[inputFor(0),inputFor(1)]);accumulator-=1/120;steps++;}
    for(const event of game.events.splice(0)){renderer.onEvent(event,game);audioEvent(event);if(event.type==='score')$('announcement').textContent=`${game.players[event.side].star.short} scores ${event.value}.`;}
    if(game.state==='ended'&&lastState!=='ended')endMatch();lastState=game.state;
    renderer.draw(game,delta);updateHud();requestAnimationFrame(frame);
  }
  renderRecord();chooseMode('solo');requestAnimationFrame(frame);
  // Expose the engine for debugging and reproducible gameplay checks.
  window.courtApp={game,start,menu,chooseMode,renderer,get cup(){return cup;},get mode(){return mode;}};
})();
