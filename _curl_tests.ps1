$base = "http://127.0.0.1:8021"
$out = @()

function Test-Curl {
    param($name, $method, $path, $body = $null)
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    $url = "$base$path"
    try {
        if ($method -eq "GET") {
            $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 30
        } else {
            $json = $body | ConvertTo-Json -Depth 10 -Compress
            $resp = Invoke-RestMethod -Uri $url -Method Post -Body $json -ContentType "application/json" -TimeoutSec 60
        }
        $pretty = $resp | ConvertTo-Json -Depth 6
        Write-Host $pretty
        return $resp
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        if ($_.Exception.Response) {
            $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $err = $sr.ReadToEnd()
            Write-Host "Response: $err" -ForegroundColor Red
        }
        return $null
    }
}

# 1. 根目录
Test-Curl "根目录信息" GET "/" | Out-Null

# 2. N皇后 - 单解
Test-Curl "N皇后(8,单解)" POST "/nqueens/solve" @{n=8; mode="one"; include_board=$true; include_stats=$true}

# 3. N皇后 - 解数
Test-Curl "N皇后(12,计数)" POST "/nqueens/solve" @{n=12; mode="count"}

# 4. N皇后 - 所有解（限制）
Test-Curl "N皇后(8,所有解,limit=5)" POST "/nqueens/solve" @{n=8; mode="all"; limit=5; include_stats=$true}

# 5. 数独 - 求解（普通难度，100ms 指标）
Write-Host "`n=== 数独求解(普通难度,100ms指标) ===" -ForegroundColor Yellow
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$medium = Test-Curl "数独普通(唯一解检查)" POST "/sudoku/solve" @{
    board_string = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
    mode = "unique"
}
$sw.Stop()
$ms = $sw.Elapsed.TotalMilliseconds
Write-Host "`n*** 普通数独总耗时(含HTTP): $([math]::Round($ms, 1))ms 目标:<100ms ***" -ForegroundColor $(if ($ms -lt 100) {"Green"} else {"Red"})

# 6. 数独 - 简单难度已填
Test-Curl "数独简单(已填完)" POST "/sudoku/solve" @{
    board_string = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
    mode = "solve"
}

# 7. 数独 - 无解检测
Test-Curl "数独无解检测" POST "/sudoku/solve" @{
    board_string = "123456789145678923789123456234567891567891234891234567345678912678912345912345678"
    mode = "unique"
}

# 8. 数独 - 多解检测
Test-Curl "数独多解检测" POST "/sudoku/solve" @{
    board_string = "123456789456789123789123456234567891567891234891234567345678912000000000000000000"
    mode = "count"
}

# 9. 数独 - 最少线索分析
Test-Curl "数独最少线索分析(普通)" POST "/sudoku/min_clues" @{
    board_string = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
}

# 10. 数独 - 难度标准
Test-Curl "数独难度标准" GET "/sudoku/standards" | Out-Null

# 11. 数独 - 生成中等难度
Write-Host "`n=== 数独生成(中等难度) ===" -ForegroundColor Yellow
$gen_sw = [System.Diagnostics.Stopwatch]::StartNew()
Test-Curl "数独生成(medium)" POST "/sudoku/generate" @{difficulty="medium"; max_attempts=50; seed=42}
$gen_sw.Stop()
Write-Host "生成耗时: $([math]::Round($gen_sw.Elapsed.TotalMilliseconds,1))ms" -ForegroundColor Cyan

# 12. 二阶魔方 - 生成打乱
$scramble = Test-Curl "魔方打乱(5步)" GET "/cube2/scramble?length=5"
if ($scramble -and $scramble.state_string) {
    $state = $scramble.state_string
    Write-Host "`n=== 二阶魔方求解(刚才打乱的 $state) ===" -ForegroundColor Yellow
    Test-Curl "魔方求解" POST "/cube2/solve" @{state_string = $state; max_depth=11; verify=$true; include_stats=$true}
}

# 13. 魔方 - 1步打乱快速测试
Write-Host "`n=== 魔方1步打乱(验证逆运算) ===" -ForegroundColor Yellow
Test-Curl "魔方1步打乱" GET "/cube2/scramble?length=1"
Test-Curl "魔方求解(验证)" POST "/cube2/solve" @{state_string="WWWWOOGOGGGBBBBRRRRYYYY"; max_depth=2; verify=$true}

# 14. 批量基准测试 - 最关键
Write-Host "`n`n========== 批量基准测试(10道混合题面) ==========" -ForegroundColor Magenta
$bench_sw = [System.Diagnostics.Stopwatch]::StartNew()
$bench = Test-Curl "批量基准测试" GET "/benchmark"
$bench_sw.Stop()
Write-Host "`n*** 基准测试总耗时: $([math]::Round($bench_sw.Elapsed.TotalMilliseconds,1))ms ***" -ForegroundColor Magenta

# 15. 100ms 单独再测一次普通数独
Write-Host "`n`n========== 最终验证: 普通难度数独 100ms 指标 ==========" -ForegroundColor $(if ($ms -lt 100) {"Green"} else {"Red"})
for ($i=1; $i -le 3; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-RestMethod -Uri "$base/sudoku/solve" -Method Post -Body (@{
        board_string = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        mode = "unique"
    } | ConvertTo-Json -Compress) -ContentType "application/json" -TimeoutSec 30
    $sw.Stop()
    $t = $sw.Elapsed.TotalMilliseconds
    $ok = $r.result -eq "unique"
    $color = if ($t -lt 100 -and $ok) {"Green"} else {"Red"}
    Write-Host "  第${i}次: $([math]::Round($t,1))ms (目标<100ms) result=$($r.result) bt=$($r.stats.backtrack_count) nodes=$($r.stats.nodes_visited)" -ForegroundColor $color
}

Write-Host "`n========== 所有验证完成 ==========" -ForegroundColor Green
