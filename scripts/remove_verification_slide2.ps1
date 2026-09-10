$p = 'C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda\docs\presentation-v2.html'
$s = [IO.File]::ReadAllText($p)
$s = $s.Replace('<div><b>07</b>검증과 확장</div>','')
$start = $s.IndexOf('<section class="s w"><div class="ey">07 · 검증과 확장</div>')
if($start -ge 0){
  $end = $s.IndexOf('</section>', $start)
  if($end -gt $start){$s = $s.Remove($start, ($end + 10) - $start)}
}
$s = $s.Replace('<span class="no">08</span></section>','<span class="no">07</span></section>')
$s = $s.Replace('<span class="no">09</span>','<span class="no">08</span>')
$s = $s.Replace('08 · 마무리 · Q&amp;A','07 · 마무리 · Q&amp;A')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))