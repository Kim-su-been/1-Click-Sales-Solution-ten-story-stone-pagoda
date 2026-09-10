$root='C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda'
$src=Join-Path $root 'docs\presentation.html';$out=Join-Path $root 'docs\presentation-v2.html'
$s=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($src))
$s=$s.Replace('<title>1-Pick Rescue Agent | 10층 석탑</title>','<title>1-pick Agent | 10층 석탑</title>').Replace('1-Pick Rescue Agent<br>10층 석탑','1-pick Agent<br>10층 석탑')
$s=$s.Replace('--muted:#6e6e73','--muted:#4c5663').Replace('--paper:#f5f5f7','--paper:#f4f0e8').Replace('body{margin:0;background:#000;color:var(--ink);','body{margin:0;background:#fbf8f2;color:var(--ink);').Replace('.slide.light{background:#fff}.slide.paper{background:var(--paper)}','.slide.light{background:#fbf8f2}.slide.paper{background:#f4f0e8}').Replace('color:#999','color:#4c5663')
$parts=$s -split '(?=<section class="slide)';$head=$parts[0];$secs=@();foreach($part in $parts[1..($parts.Count-1)]){if($part -match '10 · 검증 결과' -or $part -match '11 · 차별점과 확장'){continue};$secs+=$part}
# Remove TOC extension/verification row by generic 07 entry
for($i=0;$i -lt $secs.Count;$i++){if($secs[$i] -match 'class="toc"'){$secs[$i]=[regex]::Replace($secs[$i],'<div><b>07</b><span>.*?</span></div>','',1);$secs[$i]=$secs[$i].Replace('<div><b>08</b><span>Q&amp;A</span></div>','<div><b>12</b><span>Q&amp;A</span></div>')}}
# Replace screen section by its original position marker 07 · 화면과 시연
for($i=0;$i -lt $secs.Count;$i++){if($secs[$i] -match '07 · 화면과 시연'){$secs[$i]='<section class="slide paper"><div class="eyebrow">09 · 산출물 화면</div><h2>완성된 산출물을<br><span style="color:var(--blue)">이곳에 크게 보여줍니다.</span></h2><div class="capture" style="margin-top:40px;min-height:55vh;width:100%;font-size:18px"><div><strong style="font-size:24px">산출물 화면 삽입 영역</strong><br>산출물이 완성되면 이 영역을 실제 화면 캡처로 교체합니다.<br><span class="small">권장: 1-Pick · 상담 분석 · CRM 결과 중 핵심 화면 1장</span></div></div><div class="slide-no">09</div></section>\n';break}}
# Renumber slide footers 1..N
$n=0;for($i=0;$i -lt $secs.Count;$i++){$n++;$secs[$i]=[regex]::Replace($secs[$i],'(<div class="slide-no">)\d+(</div>)','$1'+$n+'$2',1)}
# Improve visible labels without relying on Korean matching
$body=($secs -join '')
$body=$body.Replace('10층 석탑</span>','1-pick Agent</span>')
[IO.File]::WriteAllBytes($out,[Text.Encoding]::UTF8.GetBytes($head+$body+'</main>\n</body>\n</html>'))
