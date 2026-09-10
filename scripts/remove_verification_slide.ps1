$p = 'C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda\docs\presentation-v2.html'
$s = [IO.File]::ReadAllText($p)
$s = [regex]::Replace($s, '<div><b>07</b>검증과 확장</div>', '')
$s = [regex]::Replace($s, '<section class="s w"><div class="ey">07 · 검증과 확장</div>.*?</section>\s*<section', '<section', [Text.RegularExpressions.RegexOptions]::Singleline)
$s = $s.Replace('<span class="no">08</span></section>\n<section class="s w">','<span class="no">07</span></section>\n<section class="s w">')
$s = $s.Replace('<section class="s b"><div class="ey">08 · 마무리 · Q&amp;A</div>','<section class="s b"><div class="ey">07 · 마무리 · Q&amp;A</div>')
$s = $s.Replace('<span class="no">09</span>','<span class="no">08</span>')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))