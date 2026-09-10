$root='C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda'
$src=Join-Path $root 'docs\presentation.html';$p=Join-Path $root 'docs\presentation-v2.html'
$bytes=[IO.File]::ReadAllBytes($src);$s=[Text.Encoding]::UTF8.GetString($bytes)
# Service name and contrast palette
$s=$s.Replace('<title>1-Pick Rescue Agent | 10층 석탑</title>','<title>1-pick Agent | 10층 석탑</title>').Replace('1-Pick Rescue Agent<br>10층 석탑','1-pick Agent<br>10층 석탑')
$s=$s.Replace('--muted:#6e6e73','--muted:#4c5663').Replace('--paper:#f5f5f7','--paper:#f4f0e8').Replace('body{margin:0;background:#000;color:var(--ink);','body{margin:0;background:#fbf8f2;color:var(--ink);').Replace('.slide.light{background:#fff}.slide.paper{background:var(--paper)}','.slide.light{background:#fbf8f2}.slide.paper{background:#f4f0e8}').Replace('color:#999','color:#4c5663').Replace('color:#777','color:#9aa3ad')
# Remove verification and extension slides
foreach($ey in @('10 · 검증 결과','11 · 차별점과 확장')){
  $st=$s.IndexOf('<section class="slide',$s.IndexOf($ey)-80);$en=$s.IndexOf('<section class="slide',$st+10);if($st -ge 0){if($en -lt 0){$en=$s.IndexOf('</main>',$st)};$s=$s.Substring(0,$st)+$s.Substring($en)}
}
# Remove verification/extension from TOC and fix TOC labels
$s=$s.Replace('<div><b>07</b><span>검증과 확장</span></div>','').Replace('<div><b>08</b><span>Q&amp;A</span></div>','<div><b>12</b><span>Q&amp;A</span></div>')
$s=$s.Replace('<div><b>05</b><span>어떻게 통제하는가</span></div>','<div><b>05</b><span>어떻게 통제하는가</span></div>').Replace('<div><b>06</b><span>한 사이클 시연</span></div>','<div><b>10</b><span>한 사이클 시연</span></div>').Replace('<div><b>04</b><span>개발 기술</span></div>','<div><b>08</b><span>개발 기술</span></div>')
# Renumber section labels and footer numbers
$s=$s.Replace('07 · 하네스와 근거','07 · 하네스와 근거').Replace('07 · 화면과 시연','09 · 산출물 화면').Replace('08 · 4분 30초 시연','10 · 4분 30초 시연').Replace('09 · 안전장치 시연','11 · 안전장치 시연').Replace('12 · 마무리','12 · 마무리')
$s=$s.Replace('<div class="slide-no">07</div>','<div class="slide-no">08</div>',1)
$s=$s.Replace('<div class="slide-no">09</div>','<div class="slide-no">09</div>')
$s=$s.Replace('<div class="slide-no">10</div>','<div class="slide-no">10</div>').Replace('<div class="slide-no">11</div>','<div class="slide-no">11</div>').Replace('<div class="slide-no">14</div>','<div class="slide-no">12</div>')
# Replace the screen mockup page with an intentionally empty large capture area
$cs=$s.IndexOf('<section class="slide paper">',$s.IndexOf('09 · 산출물 화면')-80);$ce=$s.IndexOf('<section class="slide',$cs+10)
if($cs -ge 0 -and $ce -gt $cs){$cap='<section class="slide paper">\n  <div class="eyebrow">09 · 산출물 화면</div><h2>완성된 산출물을<br><span style="color:var(--blue)">이곳에 크게 보여줍니다.</span></h2>\n  <div class="capture" style="margin-top:40px;min-height:55vh;width:100%;font-size:18px"><div><strong style="font-size:24px">산출물 화면 삽입 영역</strong>산출물이 완성되면 이 영역을 실제 화면 캡처로 교체합니다.<br><span class="small">권장: 1-Pick · 상담 분석 · CRM 결과 중 핵심 화면 1장</span></div></div>\n  <div class="slide-no">09</div>\n</section>\n\n';$s=$s.Substring(0,$cs)+$cap+$s.Substring($ce)}
[IO.File]::WriteAllBytes($p,[Text.Encoding]::UTF8.GetBytes($s))
