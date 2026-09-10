$p='C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda\docs\presentation-v2.html'
$s=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($p))
foreach($num in @('10','11')){$st=$s.IndexOf('<section class="slide');while($st -ge 0){$mark=$s.IndexOf('<div class="eyebrow">'+$num,$st);$next=$s.IndexOf('<section class="slide',$st+10);if($mark -ge 0 -and ($next -lt 0 -or $mark -lt $next)){ $en=$s.IndexOf('<section class="slide',$mark+10);if($en -lt 0){$en=$s.IndexOf('</main>',$mark)};$s=$s.Remove($st,$en-$st);break};if($next -lt 0){break};$st=$next}}
$s=$s.Replace('<div><b>07</b><span>검증과 확장</span></div>','').Replace('<div><b>08</b><span>Q&amp;A</span></div>','<div><b>12</b><span>Q&amp;A</span></div>')
$s=$s.Replace('<title>1-Pick Rescue Agent | 10층 석탑</title>','<title>1-pick Agent | 10층 석탑</title>').Replace('1-Pick Rescue Agent<br>10층 석탑','1-pick Agent<br>10층 석탑').Replace('10층 석탑</span><img','1-pick Agent</span><img')
$n=0;$s=[regex]::Replace($s,'<div class="slide-no">\d+</div>',{param($m) $script:n++; '<div class="slide-no">'+$script:n+'</div>'})
[IO.File]::WriteAllBytes($p,[Text.Encoding]::UTF8.GetBytes($s))
