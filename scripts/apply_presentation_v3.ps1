$p = Join-Path (Get-Location) 'docs\presentation-v2.html'
$s = [IO.File]::ReadAllText($p)
$s = $s.Replace('<title>1-Pick Rescue Agent | 10층 석탑</title>', '<title>1-pick Agent | 10층 석탑</title>')
$s = $s.Replace('background:#f7f1e7;color:#1d1d1f}.w,.p,.d,.b{background:#f7f1e7;color:#1d1d1f}', 'background:#fbf8f2;color:#14171b}.w,.p,.d,.b{background:#fbf8f2;color:#14171b}')
$s = $s.Replace('color:#6e6e73;font-weight:300', 'color:#4c5663;font-weight:400').Replace('color:#777}', 'color:#4c5663}').Replace('color:#999;font-size:12px', 'color:#4c5663;font-size:12px').Replace('color:#6e6e73;line-height:1.55', 'color:#4c5663;line-height:1.55').Replace('color:#6e6e73;margin-top:11px', 'color:#4c5663;margin-top:11px').Replace('color:#6e6e73;font-size:14px', 'color:#4c5663;font-size:14px').Replace('color:#697580;padding:20px', 'color:#34404d;padding:20px')
$s = $s.Replace('※ 시연은 별도 산출물 화면으로 진행합니다.', '※ 산출물 완성 후 화면을 크게 삽입합니다.')
$s = $s.Replace('<div><b>07</b>검증과 확장</div>', '')
$s = $s.Replace('<div><b>08</b>Q&amp;A</div>', '<div><b>07</b>Q&amp;A</div>')
$start = '<section class="s w"><div class="ey">07 · 검증과 확장</div>'
$end = '<section class="s b"><div class="ey">08 · 마무리 · Q&amp;A</div>'
$a = $s.IndexOf($start)
$b = $s.IndexOf($end)
if($a -ge 0 -and $b -gt $a){$s = $s.Remove($a,$b-$a)}
$capStart = $s.IndexOf('<section class="s p"><div class="ey">06 · 산출물 화면</div>')
$capEnd = $s.IndexOf('<section class="s b">',$capStart)
if($capStart -ge 0 -and $capEnd -gt $capStart){
  $capture = '<section class="s p"><div class="ey">06 · 산출물 화면</div><h2>완성된 산출물을<br><span style="color:#0670d8">이곳에 크게 보여줍니다.</span></h2><div class="capture-grid" style="display:block;max-width:1320px;width:100%;margin-top:38px"><div class="slot" style="min-height:52vh;width:100%;font-size:18px"><div><b style="font-size:24px">산출물 화면 삽입 영역</b><br>산출물이 완성되면 이 영역을 실제 화면 캡처로 교체합니다.<br><span class="small">권장: 1-Pick · 상담 분석 · CRM 결과 중 핵심 화면 1장</span></div></div></div><span class="no">06</span></section>\n    '
  $s = $s.Remove($capStart,$capEnd-$capStart).Insert($capStart,$capture)
}
$s = $s.Replace('<div class="ey">08 · 마무리 · Q&amp;A</div>', '<div class="ey">07 · 마무리 · Q&amp;A</div>').Replace('<span class="no">08</span>', '<span class="no">07</span>')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))
