$root='C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda'
$src=Join-Path $root 'docs\presentation.html';$p=Join-Path $root 'docs\presentation-v2.html'
$s=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($src))
$s=$s.Replace('<title>1-Pick Rescue Agent | 10층 석탑</title>','<title>1-pick Agent | 10층 석탑</title>').Replace('1-Pick Rescue Agent<br>10층 석탑','1-pick Agent<br>10층 석탑')
$s=$s.Replace('--muted:#6e6e73','--muted:#4c5663').Replace('--paper:#f5f5f7','--paper:#f4f0e8').Replace('body{margin:0;background:#000;color:var(--ink);','body{margin:0;background:#fbf8f2;color:var(--ink);').Replace('.slide.light{background:#fff}.slide.paper{background:var(--paper)}','.slide.light{background:#fbf8f2}.slide.paper{background:#f4f0e8}').Replace('color:#999','color:#4c5663')
# Remove slides with footer numbers 12 and 13 (verification / extension)
foreach($num in @('12','13')){ $pat='(?s)<section class="slide[^>]*>.*?<div class="slide-no">'+$num+'</div>.*?</section>'; $s=[regex]::Replace($s,$pat,'',1) }
# Remove TOC entry whose number is 07 (verification/extension)
$s=[regex]::Replace($s,'<div><b>07</b><span>.*?</span></div>','',1)
# Replace screen page (footer 09) with large empty area
$pat='(?s)<section class="slide[^>]*>.*?<div class="slide-no">09</div>.*?</section>'
$cap='<section class="slide paper"><div class="eyebrow">09 · OUTPUT SCREEN</div><h2>Completed output<br><span style="color:var(--blue)">will be shown here.</span></h2><div class="capture" style="margin-top:40px;min-height:55vh;width:100%;font-size:18px"><div><strong style="font-size:24px">OUTPUT SCREEN INSERT AREA</strong><br>Replace this area with the completed product screen capture.</div></div><div class="slide-no">09</div></section>'
$s=[regex]::Replace($s,$pat,$cap,1)
# Renumber visible footer numbers sequentially
$n=0;$s=[regex]::Replace($s,'<div class="slide-no">\d+</div>',{param($m) $script:n++; '<div class="slide-no">'+$script:n+'</div>'})
[IO.File]::WriteAllBytes($p,[Text.Encoding]::UTF8.GetBytes($s))
