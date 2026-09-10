$p='C:\Users\TYLI\Desktop\1-click\1-Click-Sales-Solution-ten-story-stone-pagoda\docs\presentation-v2.html'
$s=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($p))
$s=$s.Replace('1-Pick Rescue Agent','1-pick Agent')
[IO.File]::WriteAllText($p,$s,(New-Object Text.UTF8Encoding($false)))
