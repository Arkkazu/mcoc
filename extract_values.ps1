
$binFile = "C:\Users\tane1\AppData\LocalLow\Kabam\Champions\bcg\out\v1\B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin"
$outFile = "C:\python\mcoc\champions_with_values.txt"

Write-Host "バイナリ読み込み中..."
$bytes = [System.IO.File]::ReadAllBytes($binFile)
$len = $bytes.Length
Write-Host "サイズ: $([math]::Round($len/1MB,2)) MB"

Write-Host "Protobufパース中（float値含む）..."
$entries = [System.Collections.Generic.List[object]]::new()
$i = 0

while ($i -lt $len - 10) {
    if ($bytes[$i] -ne 0x0A) { $i++; continue }
    $i++
    $outerLen = 0; $shift = 0; $j = $i
    do {
        if ($j -ge $len) { break }
        $b = $bytes[$j]; $j++
        $outerLen = $outerLen -bor (($b -band 0x7F) -shl $shift); $shift += 7
    } while ($b -band 0x80)
    if ($outerLen -lt 5 -or $outerLen -gt 200000 -or ($j + $outerLen) -gt $len) { continue }
    $msgEnd = $j + $outerLen
    if ($bytes[$j] -ne 0x0A) { continue }
    $j++
    $idLen = 0; $s2 = 0
    do { $b = $bytes[$j]; $j++; $idLen = $idLen -bor (($b -band 0x7F) -shl $s2); $s2 += 7 } while ($b -band 0x80)
    if ($idLen -lt 3 -or $idLen -gt 100 -or ($j + $idLen) -gt $len) { continue }
    $idBytes = $bytes[$j..($j + $idLen - 1)]
    $allP = $true
    foreach ($b in $idBytes) { if ($b -lt 0x20 -or $b -gt 0x7E) { $allP = $false; break } }
    if (-not $allP) { continue }
    $id = [System.Text.Encoding]::ASCII.GetString($idBytes)
    if ($id -notmatch '^[a-zA-Z][a-zA-Z0-9_]+$') { continue }
    $j += $idLen

    $f2 = ""; $f3 = ""; $f4 = ""; $f5 = ""; $f7 = ""; $f11 = ""; $f12 = ""
    $f8 = $null; $f9 = $null
    $f10 = $null; $f13 = $null; $f14 = $null; $f15 = $null
    $fc = 0
    while ($j -lt $msgEnd -and $fc -lt 50) {
        $fc++
        if ($j -ge $msgEnd) { break }
        $tb = $bytes[$j]; $j++
        $wt = $tb -band 7
        # varint field number (handles 2-byte tags)
        $fn = $tb -shr 3
        if ($tb -band 0x80) {
            # 2-byte tag
            if ($j -ge $msgEnd) { break }
            $tb2 = $bytes[$j]; $j++
            $fn = (($tb -band 0x7F) -shr 3) -bor (($tb2 -band 0x7F) -shl 4)
        }

        if ($wt -eq 2) {
            $fL = 0; $fs = 0
            do {
                if ($j -ge $msgEnd) { break }
                $b = $bytes[$j]; $j++; $fL = $fL -bor (($b -band 0x7F) -shl $fs); $fs += 7
            } while ($b -band 0x80)
            if ($fL -lt 0 -or $fL -gt 50000 -or ($j + $fL) -gt $msgEnd) { break }
            if ($fL -ge 1 -and $fL -le 500) {
                $fb = $bytes[$j..($j + $fL - 1)]
                $isP = $true
                foreach ($b in $fb) { if ($b -lt 0x09 -or ($b -gt 0x0D -and $b -lt 0x20) -or $b -gt 0x7E) { $isP = $false; break } }
                if ($isP) {
                    $sv = [System.Text.Encoding]::ASCII.GetString($fb)
                    if ($fn -eq 2 -and $f2 -eq "") { $f2 = $sv }
                    elseif ($fn -eq 3 -and $f3 -eq "") { $f3 = $sv }
                    elseif ($fn -eq 4 -and $f4 -eq "") { $f4 = $sv }
                    elseif ($fn -eq 5 -and $f5 -eq "") { $f5 = $sv }
                    elseif ($fn -eq 7 -and $f7 -eq "") { $f7 = $sv }
                    elseif ($fn -eq 11 -and $f11 -eq "") { $f11 = $sv }
                    elseif ($fn -eq 12 -and $f12 -eq "") { $f12 = $sv }
                }
            }
            $j += $fL
        } elseif ($wt -eq 0) {
            $iv = 0; $is2 = 0
            do {
                if ($j -ge $msgEnd) { break }
                $b = $bytes[$j]; $j++
                $iv = $iv -bor (($b -band 0x7F) -shl $is2); $is2 += 7
            } while ($b -band 0x80)
            if ($fn -eq 8 -and $null -eq $f8) { $f8 = $iv }
            elseif ($fn -eq 9 -and $null -eq $f9) { $f9 = $iv }
        } elseif ($wt -eq 5) {
            if (($j + 4) -le $msgEnd) {
                $fv = [System.BitConverter]::ToSingle($bytes, $j)
                if ($fn -eq 10 -and $null -eq $f10) { $f10 = $fv }
                elseif ($fn -eq 13 -and $null -eq $f13) { $f13 = $fv }
                elseif ($fn -eq 14 -and $null -eq $f14) { $f14 = $fv }
                elseif ($fn -eq 15 -and $null -eq $f15) { $f15 = $fv }
            }
            $j += 4
        } elseif ($wt -eq 1) { $j += 8
        } else { break }
    }
    $entries.Add([PSCustomObject]@{
        Id=$id; Type=$f2; Condition=$f3; Trigger=$f4; Filter=$f5
        Var=$f7; Cond2=$f11; DisplayId=$f12
        Flag8=$f8; Flag9=$f9
        Val0=$f10; Val1=$f13; Val2=$f14; Val3=$f15
    })
    $i = $msgEnd
}

Write-Host "エントリー数: $($entries.Count)"
$hasVals = ($entries | Where-Object { $null -ne $_.Val1 -or $null -ne $_.Val2 }).Count
Write-Host "性能値あり: $hasVals"

# チャンピオン名マッピング
$champMap = @{}
$champMap['abim'] = 'Abomination (Immortal)'
$champMap['abomination'] = 'Abomination'
$champMap['absorbingman'] = 'Absorbing Man'
$champMap['abyss'] = 'Abyss'
$champMap['adam'] = 'Adam Warlock'
$champMap['adamwarlock'] = 'Adam Warlock'
$champMap['adaptoid'] = 'Super-Adaptoid'
$champMap['aeg'] = 'Aegon'
$champMap['aegon'] = 'Aegon'
$champMap['agentvenom'] = 'Agent Venom'
$champMap['agv'] = 'Agent Venom'
$champMap['airwalker'] = 'Air-Walker'
$champMap['amcha'] = 'America Chavez'
$champMap['anni'] = 'Annihilus'
$champMap['antfu'] = 'Ant-Man (Future Variant)'
$champMap['antman'] = 'Ant-Man'
$champMap['antivenom'] = 'Anti-Venom'
$champMap['antisbt'] = 'Anti-Venom'
$champMap['apo'] = 'Apocalypse'
$champMap['apocalypse'] = 'Apocalypse'
$champMap['ares'] = 'Ares'
$champMap['arc'] = 'Arcade'
$champMap['archangel'] = 'Archangel'
$champMap['atma'] = 'Archangel'
$champMap['ava'] = 'White Tiger (Ava Ayala)'
$champMap['avx'] = 'Alliance vs X-Men (Content)'
$champMap['aw'] = 'Alliance War (Content)'
$champMap['aol'] = 'Act of Legacy (Content)'
$champMap['a1'] = 'Tutorial Data'
$champMap['a8'] = 'Act 8 Content'
$champMap['bast'] = 'Bast'
$champMap['beast'] = 'Beast'
$champMap['bhmt'] = 'Black Hammer (Boss)'
$champMap['bishn'] = 'Bishop'
$champMap['bishop'] = 'Bishop'
$champMap['blade'] = 'Blade'
$champMap['blumrvl'] = 'Blue Marvel'
$champMap['bull'] = 'Bullseye'
$champMap['bullseye'] = 'Bullseye'
$champMap['capb'] = 'Captain Britain'
$champMap['capsw'] = 'Captain America (Sam Wilson)'
$champMap['carserp'] = 'Serpent (Car Boss)'
$champMap['cassie'] = 'Cassie Lang'
$champMap['col'] = 'Colossus'
$champMap['colossus'] = 'Colossus'
$champMap['cnef'] = 'Count Nefaria'
$champMap['cnova'] = 'Nova (Captain)'
$champMap['crv'] = 'Corvus Glaive'
$champMap['cvbw'] = 'Black Widow (Civil War)'
$champMap['cyc90'] = 'Cyclops (90s)'
$champMap['cyclops'] = 'Cyclops'
$champMap['dani'] = 'Dani Moonstar'
$champMap['daz'] = 'Dazzler'
$champMap['dbotu'] = 'Doctor Doom (Bot)'
$champMap['ded'] = 'Deadpool'
$champMap['dom'] = 'Domino'
$champMap['doom'] = 'Doctor Doom'
$champMap['dor'] = 'Dormammu'
$champMap['dormammu'] = 'Dormammu'
$champMap['dplplat'] = 'Deadpool (Platpool)'
$champMap['drac'] = 'Dracula'
$champMap['dracula'] = 'Dracula'
$champMap['drstrange'] = 'Doctor Strange'
$champMap['dust'] = 'Dust'
$champMap['dthns'] = 'Deathtrap'
$champMap['dun'] = 'Dungeons (Content)'
$champMap['elsa'] = 'Elsa Bloodstone'
$champMap['elsabloodstone'] = 'Elsa Bloodstone'
$champMap['emma'] = 'Emma Frost'
$champMap['emmafrost'] = 'Emma Frost'
$champMap['f4'] = 'Fantastic Four Saga'
$champMap['frnk'] = 'Franken-Castle'
$champMap['galan'] = 'Galan'
$champMap['ghru'] = 'Ghost Rider (Universe)'
$champMap['ghostrider'] = 'Ghost Rider'
$champMap['glad'] = 'Gladiator'
$champMap['gladiator'] = 'Gladiator'
$champMap['glyk'] = 'Glykon'
$champMap['gmast'] = 'Grandmaster'
$champMap['gmaster'] = 'Grandmaster'
$champMap['grndmstr'] = 'Grandmaster'
$champMap['gorr'] = 'Gorr the God Butcher'
$champMap['gp'] = 'System Global Passive'
$champMap['guard'] = 'Guardsman'
$champMap['guardsman'] = 'Guardsman'
$champMap['heim'] = 'Heimdall'
$champMap['heimdall'] = 'Heimdall'
$champMap['herc'] = 'Hercules'
$champMap['hercules'] = 'Hercules'
$champMap['highevo'] = 'High Evolutionary'
$champMap['hitmon'] = 'Hit-Monkey'
$champMap['hitmonkey'] = 'Hit-Monkey'
$champMap['hlklng'] = 'Hulkling'
$champMap['hulkim'] = 'Hulk (Immortal)'
$champMap['hulkrag'] = 'Hulk (Ragnarok)'
$champMap['hvk'] = 'Havok'
$champMap['havok'] = 'Havok'
$champMap['hyp'] = 'Hyperion'
$champMap['hyperion'] = 'Hyperion'
$champMap['iheart'] = 'Iron Heart'
$champMap['iim'] = 'Iron Man (Infamous)'
$champMap['invwo'] = 'Invisible Woman'
$champMap['ironfist'] = 'Iron Fist'
$champMap['ironman'] = 'Iron Man'
$champMap['jess'] = 'Jessica Jones'
$champMap['jjj'] = 'J. Jonah Jameson'
$champMap['jub'] = 'Jubilee'
$champMap['jubilee'] = 'Jubilee'
$champMap['joov'] = 'Jubilee (Variant)'
$champMap['kangimp'] = 'Kang (Impostor)'
$champMap['kangsup'] = 'Kang (Superior)'
$champMap['kate'] = 'Kate Bishop'
$champMap['korg'] = 'Korg'
$champMap['krvn'] = 'Karven'
$champMap['ktyp'] = 'King Thor'
$champMap['ld'] = 'Lady Deathstrike'
$champMap['leader'] = 'The Leader'
$champMap['lotan'] = 'Leviathon Tide'
$champMap['luma'] = 'Luma'
$champMap['magik'] = 'Magik'
$champMap['maes'] = 'Maestro'
$champMap['maestro'] = 'Maestro'
$champMap['mady'] = 'Madelyne Pryor'
$champMap['maker'] = 'The Maker'
$champMap['mantis'] = 'Mantis'
$champMap['mbaku'] = 'M-Baku'
$champMap['mgnx'] = 'Magneto (X-Men)'
$champMap['mkt'] = 'Makkari'
$champMap['mls'] = 'Mole Man'
$champMap['morb'] = 'Morbius'
$champMap['mojo'] = 'Mojo'
$champMap['mrkn'] = 'Mr. Knuckles'
$champMap['mysto'] = 'Mysterio'
$champMap['nam'] = 'Namor'
$champMap['namor'] = 'Namor'
$champMap['nec'] = 'Necropolis (Content)'
$champMap['nmaster'] = 'Nightmare (Master)'
$champMap['nrthstr'] = 'Northstar'
$champMap['northstar'] = 'Northstar'
$champMap['nico'] = 'Nico Minoru'
$champMap['nim'] = 'Nimrod'
$champMap['nova'] = 'Nova'
$champMap['odin'] = 'Odin'
$champMap['onslght'] = 'Onslaught'
$champMap['onslaught'] = 'Onslaught'
$champMap['ore'] = 'Omega Red'
$champMap['ored'] = 'Omega Red'
$champMap['oro'] = 'Storm (Ororo Variant)'
$champMap['osntl'] = 'Old Man Logan'
$champMap['peni'] = 'Peni Parker'
$champMap['phx'] = 'Phoenix'
$champMap['phoenix'] = 'Phoenix'
$champMap['photon'] = 'Photon'
$champMap['pixie'] = 'Pixie'
$champMap['pnshru'] = 'Punisher 2099'
$champMap['profx'] = 'Professor X'
$champMap['proxima'] = 'Proxima Midnight'
$champMap['prowl'] = 'Prowler'
$champMap['psymn'] = 'Psylocke'
$champMap['ptrt'] = 'Patriot'
$champMap['purg'] = 'Purgatory'
$champMap['pve'] = 'PVE Content'
$champMap['pvitr'] = 'Colossus (Piotr Variant)'
$champMap['qckslvr'] = 'Quicksilver'
$champMap['raid'] = 'Raids (Content)'
$champMap['redg'] = 'Red Guardian'
$champMap['reed'] = 'Mister Fantastic'
$champMap['rgob'] = 'Red Goblin'
$champMap['rokt'] = 'Rocket Raccoon'
$champMap['rogue'] = 'Rogue'
$champMap['ruby'] = 'Ruby Thursday'
$champMap['sand'] = 'Sandman'
$champMap['sb'] = 'Story Battle (Content)'
$champMap['scrm'] = 'Scream'
$champMap['scrpn'] = 'Scorpion'
$champMap['scytalis'] = 'Scytalis'
$champMap['sentinel'] = 'Sentinel'
$champMap['sentibot'] = 'Sentinel Bot'
$champMap['sentineloid'] = 'Sentineloid (Boss)'
$champMap['sentry'] = 'Sentry'
$champMap['sersi'] = 'Sersi'
$champMap['shang'] = 'Shang-Chi'
$champMap['shuri'] = 'Shuri'
$champMap['shthra'] = 'She-Hulk (Thanos Variant)'
$champMap['silk'] = 'Silk'
$champMap['skrull'] = 'Skrull'
$champMap['solv'] = 'Solvang'
$champMap['sorcsup'] = 'Sorcerer Supreme'
$champMap['spdr2099'] = 'Spider-Man 2099'
$champMap['spdrsprm'] = 'Spider-Man Supreme'
$champMap['spdrwmn'] = 'Spider-Woman'
$champMap['spham'] = 'Spider-Ham'
$champMap['spiderman'] = 'Spider-Man'
$champMap['spot'] = 'The Spot'
$champMap['sprl'] = 'Spiral'
$champMap['spunk'] = 'Spunk'
$champMap['sqch'] = 'Squirrel Girl'
$champMap['squirrelgirl'] = 'Squirrel Girl'
$champMap['srpnt'] = 'Serpent'
$champMap['ssable'] = 'Silver Sable'
$champMap['stlspdr'] = 'Steel Spider'
$champMap['stormr'] = 'Storm (Rogue Variant)'
$champMap['strf'] = 'Stryfe'
$champMap['supman'] = 'Cosmic Spider-Man'
$champMap['surf'] = 'Silver Surfer'
$champMap['swtch'] = 'Switch'
$champMap['tbe'] = 'Thor (Binary Variant)'
$champMap['terry'] = 'Terrax'
$champMap['tg'] = 'Tag System'
$champMap['thanos'] = 'Thanos'
$champMap['thechamp'] = 'The Champion'
$champMap['thing'] = 'The Thing'
$champMap['tnia'] = 'Titania'
$champMap['toad'] = 'Toad'
$champMap['torch'] = 'Human Torch'
$champMap['tm'] = 'Taskmaster'
$champMap['viv'] = 'Viv Vision'
$champMap['void'] = 'The Void'
$champMap['vox'] = 'Vox'
$champMap['vtd'] = 'Venompool'
$champMap['warmac'] = 'War Machine'
$champMap['wave'] = 'Wave'
$champMap['whttgr'] = 'White Tiger'
$champMap['wong'] = 'Wong'
$champMap['wrlk'] = 'Warlock'
$champMap['wwolf'] = 'Werewolf by Night'
$champMap['x23'] = 'X-23'
$champMap['x23u'] = 'X-23 (Uncanny)'
$champMap['ylb'] = 'Yellowjacket'
$champMap['zemo'] = 'Baron Zemo'
$champMap['zola'] = 'Arnim Zola'
$champMap['bong'] = 'Bong (Boss)'
$champMap['buddy'] = 'Buddy (Boss)'
$champMap['carl'] = 'Carl (Boss)'
$champMap['ceras'] = 'Ceras (Boss)'
$champMap['hnchpl'] = 'Henchman (Chapel)'
$champMap['iphyne'] = 'Iphyne (Boss)'
$champMap['karrie'] = 'Karrie'
$champMap['npc'] = 'NPC Enemy'
$champMap['ave'] = 'Avengers (Synergy/Content)'
$champMap['mdk'] = 'Mordok'
$champMap['amra'] = 'Amra'

Write-Host "グループ化中..."
$groups = $entries | Group-Object { ($_.Id -split '_')[0] } | Sort-Object Name

Write-Host "ファイル書き込み中..."
$sw = [System.IO.StreamWriter]::new($outFile, $false, [System.Text.Encoding]::UTF8)
$eq80 = "=" * 80
$dsh80 = "-" * 80

$sw.WriteLine($eq80)
$sw.WriteLine("Marvel Contest of Champions - チャンピオン全アビリティデータ（性能値付き）")
$sw.WriteLine("ファイル: B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin")
$sw.WriteLine("総エントリー数: $($entries.Count)  |  グループ数: $($groups.Count)")
$sw.WriteLine("フィールド: ID | 効果タイプ(F2) | トリガー(F4) | Val1(F13) | Val2(F14) | Val3(F15) | 条件(F3) | フィルター(F5)")
$sw.WriteLine($eq80)

foreach ($grp in $groups) {
    $prefix = $grp.Name
    $fullName = if ($champMap.ContainsKey($prefix)) { $champMap[$prefix] } else { "(不明)" }
    $sw.WriteLine("")
    $sw.WriteLine($eq80)
    $sw.WriteLine("チャンピオン: $fullName  [prefix: $prefix]  (エントリー数: $($grp.Count))")
    $sw.WriteLine($dsh80)
    foreach ($e in ($grp.Group | Sort-Object { $_.Id })) {
        $v1 = if ($null -ne $e.Val1) { [math]::Round($e.Val1, 4).ToString() } else { "" }
        $v2 = if ($null -ne $e.Val2) { [math]::Round($e.Val2, 4).ToString() } else { "" }
        $v3 = if ($null -ne $e.Val3) { [math]::Round($e.Val3, 4).ToString() } else { "" }
        $sw.WriteLine("  " + $e.Id.PadRight(50) + $e.Type.PadRight(22) + $e.Trigger.PadRight(22) + $v1.PadRight(12) + $v2.PadRight(12) + $v3)
        if ($e.Condition -ne "" -and $e.Condition.Length -lt 300) {
            $sw.WriteLine("    >> 条件: " + $e.Condition)
        }
        if ($e.Filter -ne "" -and $e.Filter.Length -lt 300) {
            $sw.WriteLine("    >> フィルター: " + $e.Filter)
        }
        if ($e.Var -ne "") {
            $sw.WriteLine("    >> 変数: " + $e.Var)
        }
    }
}
$sw.Close()

$fi = Get-Item $outFile
Write-Host "完了: $outFile ($([math]::Round($fi.Length/1MB,2)) MB)"
