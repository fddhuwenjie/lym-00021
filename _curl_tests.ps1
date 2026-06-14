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

Write-Host "`n`n========== 新增功能验证 ==========" -ForegroundColor Magenta

# 16. N皇后 N=14 解计数 (目标 365596, 5秒内)
Write-Host "`n=== N皇后 N=14 解计数 (目标: 365596, 5秒内) ===" -ForegroundColor Yellow
$n14_sw = [System.Diagnostics.Stopwatch]::StartNew()
$n14_result = Test-Curl "N皇后 N=14 计数" POST "/api/count" @{
    problem_type = "nqueens"
    n = 14
}
$n14_sw.Stop()
$n14_ms = $n14_sw.Elapsed.TotalMilliseconds
$n14_ok = $n14_result -and $n14_result.solution_count -eq 365596 -and $n14_ms -lt 5000
Write-Host "*** N皇后 N=14: 解数=$($n14_result.solution_count) 耗时=$([math]::Round($n14_ms,1))ms 目标:<5000ms, 解数=365596 ***" -ForegroundColor $(if ($n14_ok) {"Green"} else {"Red"})

# 17. 数独解计数
Write-Host "`n=== 数独解计数 (上限1000) ===" -ForegroundColor Cyan
Test-Curl "数独解计数" POST "/api/count" @{
    problem_type = "sudoku"
    board_string = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
}

# 18. 二阶魔方最短路径计数
Write-Host "`n=== 二阶魔方最短路径计数 ===" -ForegroundColor Cyan
Test-Curl "二阶魔方最短路径计数" POST "/api/count" @{
    problem_type = "cube2"
    state_string = "WWWWOOGOGGGBBBBRRRRYYYY"
    max_depth = 11
}

# 19. 三阶魔方状态验证
Write-Host "`n=== 三阶魔方状态验证 ===" -ForegroundColor Cyan
Test-Curl "三阶魔方已还原状态验证" POST "/api/cube3/validate" @{
    state_string = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
}

# 20. 通用CSP引擎 - 4色图着色
Write-Host "`n=== 通用CSP引擎 - 4色图着色 ===" -ForegroundColor Yellow
$csp_sw = [System.Diagnostics.Stopwatch]::StartNew()
$graph_coloring = Test-Curl "4色图着色" POST "/api/csp/solve" @{
    problem = @{
        variables = @("WA", "NT", "SA", "Q", "NSW", "V", "T")
        domains = @{
            WA = @(0, 1, 2, 3)
            NT = @(0, 1, 2, 3)
            SA = @(0, 1, 2, 3)
            Q = @(0, 1, 2, 3)
            NSW = @(0, 1, 2, 3)
            V = @(0, 1, 2, 3)
            T = @(0, 1, 2, 3)
        }
        constraints = @(
            @{ type = "all_different"; variables = @("WA", "NT") }
            @{ type = "all_different"; variables = @("WA", "SA") }
            @{ type = "all_different"; variables = @("NT", "SA") }
            @{ type = "all_different"; variables = @("NT", "Q") }
            @{ type = "all_different"; variables = @("SA", "Q") }
            @{ type = "all_different"; variables = @("SA", "NSW") }
            @{ type = "all_different"; variables = @("SA", "V") }
            @{ type = "all_different"; variables = @("Q", "NSW") }
            @{ type = "all_different"; variables = @("NSW", "V") }
        )
    }
    mode = "one"
}
$csp_sw.Stop()
$csp_ok = $graph_coloring -and $graph_coloring.solution_count -ge 1
Write-Host "*** 4色图着色: 解数=$($graph_coloring.solution_count) 耗时=$([math]::Round($csp_sw.Elapsed.TotalMilliseconds,1))ms ***" -ForegroundColor $(if ($csp_ok) {"Green"} else {"Red"})

# 21. 通用CSP引擎 - 全部解
Write-Host "`n=== 通用CSP引擎 - 4色图着色全部解 ===" -ForegroundColor Cyan
Test-Curl "4色图着色全部解" POST "/api/csp/solve" @{
    problem = @{
        variables = @("WA", "NT", "SA", "Q", "NSW", "V", "T")
        domains = @{
            WA = @(0, 1, 2, 3)
            NT = @(0, 1, 2, 3)
            SA = @(0, 1, 2, 3)
            Q = @(0, 1, 2, 3)
            NSW = @(0, 1, 2, 3)
            V = @(0, 1, 2, 3)
            T = @(0, 1, 2, 3)
        }
        constraints = @(
            @{ type = "all_different"; variables = @("WA", "NT") }
            @{ type = "all_different"; variables = @("WA", "SA") }
            @{ type = "all_different"; variables = @("NT", "SA") }
            @{ type = "all_different"; variables = @("NT", "Q") }
            @{ type = "all_different"; variables = @("SA", "Q") }
            @{ type = "all_different"; variables = @("SA", "NSW") }
            @{ type = "all_different"; variables = @("SA", "V") }
            @{ type = "all_different"; variables = @("Q", "NSW") }
            @{ type = "all_different"; variables = @("NSW", "V") }
        )
    }
    mode = "all"
    solution_limit = 100
}

# 22. 通用CSP引擎 - 预置实例
Write-Host "`n=== 通用CSP引擎 - 预置实例 ===" -ForegroundColor Cyan
Test-Curl "CSP预置实例" GET "/api/csp/examples" | Out-Null

# 23. 三阶魔方求解 - 已知20步最优解 (superflip)
Write-Host "`n=== 三阶魔方求解 - Superflip (20步最优解, 30秒内) ===" -ForegroundColor Yellow
$cube3_sw = [System.Diagnostics.Stopwatch]::StartNew()
$cube3_result = Test-Curl "三阶魔方 Superflip" POST "/api/cube3/solve" @{
    state_string = "UUFUUFUUFURRURRURRFFFFFFFFFDDDDDDDDDLLBLLBLLBBBBBBBBB"
    max_depth = 20
    verify = $true
}
$cube3_sw.Stop()
$cube3_ms = $cube3_sw.Elapsed.TotalMilliseconds
$cube3_ok = $cube3_result -and $cube3_result.move_count -le 20 -and $cube3_ms -lt 30000
if ($cube3_result) {
    Write-Host "*** 三阶魔方: 步数=$($cube3_result.move_count) 耗时=$([math]::Round($cube3_ms,1))ms 验证=$($cube3_result.verified) 目标:≤20步, <30000ms ***" -ForegroundColor $(if ($cube3_ok -and $cube3_result.verified) {"Green"} else {"Red"})
}

Write-Host "`n========== 新增功能验证完成 ==========" -ForegroundColor Green

Write-Host "`n========== 所有验证完成 ==========" -ForegroundColor Green
