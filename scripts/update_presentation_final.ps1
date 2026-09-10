$p = 'C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda\docs\presentation-v2.html'
$s = [IO.File]::ReadAllText($p)
$s = $s.Replace('body{margin:0;background:#000;color:#1d1d1f;font-family:', 'body{margin:0;background:#f7f1e7;color:#1d1d1f;font-family:')
$s = $s.Replace('overflow:hidden}.w{background:#fff}.p{background:#f5f5f7}.d{background:#272729;color:#fff}.b{background:#000;color:#fff}', 'overflow:hidden;background:#f7f1e7;color:#1d1d1f}.w,.p,.d,.b{background:#f7f1e7;color:#1d1d1f}')
$s = $s.Replace('<div><b>07</b>검증과 확장</div>','')
$start = '<section class="s w"><div class="ey">07 · 검증과 확장</div>'
$end = '<section class="s b"><div class="ey">08 · 마무리 · Q&amp;A</div>'
$a = $s.IndexOf($start)
$b = $s.IndexOf($end)
if($a -ge 0 -and $b -gt $a){$s = $s.Remove($a,$b-$a)}
$s = $s.Replace('08 · 산출물 화면','06 · 산출물 화면').Replace('09</span></section>','08</span></section>').Replace('08 · 마무리 · Q&amp;A','07 · 마무리 · Q&amp;A').Replace('<span class="no">10</span>','<span class="no">09</span>')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))