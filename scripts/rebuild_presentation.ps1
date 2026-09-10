$root='C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda'
$src=Join-Path $root 'docs\presentation.html';$p=Join-Path $root 'docs\presentation-v2.html'
Copy-Item $src $p -Force
$bytes=[IO.File]::ReadAllBytes($p);$s=[Text.Encoding]::UTF8.GetString($bytes)
$s=$s.Replace('<title>1-Pick Rescue Agent | 10층 석탑</title>','<title>1-pick Agent | 10층 석탑</title>').Replace('1-Pick Rescue Agent<br>10층 석탑','1-pick Agent<br>10층 석탑')
$s=$s.Replace('<div><b>07</b>검증과 확장</div>','').Replace('※ 시연은 별도 산출물 화면으로 진행합니다.','※ 산출물 완성 후 화면을 크게 삽입합니다.')
$st=$s.IndexOf('<section class="slide"><div class="eyebrow">07');if($st -lt 0){$st=$s.IndexOf('<section class="slide paper"><div class="eyebrow">07')}if($st -ge 0){$en=$s.IndexOf('<section class="slide',$st+10);if($en -gt $st){$s=$s.Substring(0,$st)+$s.Substring($en)}}
$s=$s.Replace('<div><b>07</b><span>검증과 확장</span></div>','').Replace('<div><b>08</b><span>Q&amp;A</span></div>','<div><b>07</b><span>Q&amp;A</span></div>').Replace('08 · 마무리 · Q&amp;A','07 · 마무리 · Q&amp;A').Replace('<div class="slide-no">08</div>','<div class="slide-no">07</div>')
$s=$s.Replace('body{margin:0;background:#000;color:var(--ink);','body{margin:0;background:#fbf8f2;color:var(--ink);').Replace('.slide.light{background:#fff}.slide.paper{background:var(--paper)}','.slide.light{background:#fbf8f2}.slide.paper{background:#f4f0e8}').Replace('--muted:#6e6e73','--muted:#4c5663').Replace('color:#999','color:#4c5663').Replace('color:#aaa','color:#c5cbd3')
[IO.File]::WriteAllBytes($p,[Text.Encoding]::UTF8.GetBytes($s))
