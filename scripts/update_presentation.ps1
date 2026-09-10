$p = Join-Path (Get-Location) 'docs\presentation-v2.html'
$s = [IO.File]::ReadAllText($p)
$old = "html{scroll-snap-type:y mandatory}body{margin:0;background:#000;color:#1d1d1f;font-family:'우리다움 R',system-ui,sans-serif}.s{min-height:100vh;scroll-snap-align:start;position:relative;padding:7vh 7.5vw;display:flex;flex-direction:column;justify-content:center;overflow:hidden}.w{background:#fff}.p{background:#f5f5f7}.d{background:#272729;color:#fff}.b{background:#000;color:#fff}"
$new = "html{scroll-snap-type:y mandatory}body{margin:0;background:#f7f1e7;color:#1d1d1f;font-family:'우리다움 R',system-ui,sans-serif}.s{min-height:100vh;scroll-snap-align:start;position:relative;padding:7vh 7.5vw;display:flex;flex-direction:column;justify-content:center;overflow:hidden;background:#f7f1e7;color:#1d1d1f}.w,.p,.d,.b{background:#f7f1e7;color:#1d1d1f}"
$s = $s.Replace($old,$new)
$s = $s.Replace('<div><b>07</b>검증과 확장</div>','')
$start = '<section class="s w"><div class="ey">07 · 검증과 확장</div>'
$end = '<section class="s b"><div class="ey">08 · 마무리 · Q&amp;A</div>'
$a = $s.IndexOf($start)
$b = $s.IndexOf($end)
if($a -ge 0 -and $b -gt $a){$s = $s.Remove($a,$b-$a)}
$s = $s.Replace('08 · 산출물 화면','06 · 산출물 화면')
$s = $s.Replace('09</span></section>','08</span></section>')
$s = $s.Replace('08 · 마무리 · Q&amp;A','07 · 마무리 · Q&amp;A')
$s = $s.Replace('<span class="no">10</span>','<span class="no">09</span>')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))