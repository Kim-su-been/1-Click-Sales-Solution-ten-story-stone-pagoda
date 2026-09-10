$p = 'C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda\docs\presentation-v2.html'
$s = [IO.File]::ReadAllText($p)
$needle = '검증과 확장'
while(($i = $s.IndexOf($needle)) -ge 0){
  $sectionStart = $s.LastIndexOf('<section', $i)
  $sectionEnd = $s.IndexOf('</section>', $i)
  if($sectionStart -lt 0 -or $sectionEnd -lt 0){break}
  $s = $s.Remove($sectionStart, ($sectionEnd + 10) - $sectionStart)
}
$s = $s.Replace('<span class="no">08</span></section>','<span class="no">07</span></section>')
$s = $s.Replace('<span class="no">09</span>','<span class="no">08</span>')
$s = $s.Replace('08 · 마무리 · Q&amp;A','07 · 마무리 · Q&amp;A')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))