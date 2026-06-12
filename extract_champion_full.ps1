
$binFile = "C:\Users\tane1\AppData\LocalLow\Kabam\Champions\bcg\out\v1\B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin"
$outFile = "C:\python\mcoc\champion_full_data.txt"

Write-Host "バイナリ読み込み中..."
$bytes = [System.IO.File]::ReadAllBytes($binFile)
$len = $bytes.Length
Write-Host "サイズ: $([math]::Round($len/1MB,2)) MB"

# ===== 1. アビリティエントリを解析 =====
Write-Host "アビリティ解析中..."
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

    $f2 = ""; $f3 = ""; $f4 = ""; $f5 = ""; $f7 = ""
    $f13 = $null; $f14 = $null; $f15 = $null
    $fc = 0
    while ($j -lt $msgEnd -and $fc -lt 50) {
        $fc++
        if ($j -ge $msgEnd) { break }
        $tb = $bytes[$j]; $j++
        $wt = $tb -band 7
        $fn = $tb -shr 3
        if ($tb -band 0x80) {
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
                }
            }
            $j += $fL
        } elseif ($wt -eq 0) {
            do { if ($j -ge $msgEnd) { break }; $b = $bytes[$j]; $j++ } while ($b -band 0x80)
        } elseif ($wt -eq 5) {
            if (($j + 4) -le $msgEnd) {
                $fv = [System.BitConverter]::ToSingle($bytes, $j)
                if ($fn -eq 13 -and $null -eq $f13) { $f13 = $fv }
                elseif ($fn -eq 14 -and $null -eq $f14) { $f14 = $fv }
                elseif ($fn -eq 15 -and $null -eq $f15) { $f15 = $fv }
            }
            $j += 4
        } elseif ($wt -eq 1) { $j += 8
        } else { break }
    }
    $entries.Add([PSCustomObject]@{
        Id=$id; Type=$f2; Condition=$f3; Trigger=$f4; Filter=$f5; Var=$f7
        V1=$f13; V2=$f14; V3=$f15
    })
    $i = $msgEnd
}
Write-Host "アビリティエントリ数: $($entries.Count)"

# ===== 2. チャンピオン定義セクションからクラスを抽出 =====
Write-Host "クラス情報抽出中..."
$sb = [System.Text.StringBuilder]::new()
for ($idx = 15000000; $idx -lt [Math]::Min($len, 20000000); $idx++) {
    $b = $bytes[$idx]
    if (($b -ge 0x61 -and $b -le 0x7A) -or ($b -ge 0x30 -and $b -le 0x39) -or $b -eq 0x5F) {
        $sb.Append([char]$b) | Out-Null
    } else { $sb.Append(' ') | Out-Null }
}
$defText = $sb.ToString()
$clsPat = "([a-z][a-z0-9_]+?)_(cm|un|rar|ep|leg|t6|t7) +([a-z][a-z0-9_]+?) +(mutant|cosmic|tech|skill|science|mystic) +(common|uncommon|rare|epic|legendary)"
$clsMatches = [regex]::Matches($defText, $clsPat)
$champClass = @{}
foreach ($m in $clsMatches) {
    $baseId = $m.Groups[3].Value
    $cls = $m.Groups[4].Value
    if (-not $champClass.ContainsKey($baseId)) { $champClass[$baseId] = $cls }
}
Write-Host "クラス定義数: $($champClass.Count)"

# ===== 3. チャンピオン名マッピング =====
$champMap = @{}
$champMap['abim'] = 'Abomination (Immortal)'
$champMap['abomination'] = 'Abomination'
$champMap['absorbingman'] = 'Absorbing Man'
$champMap['abyss'] = 'Abyss'
$champMap['adamwarlock'] = 'Adam Warlock'
$champMap['adaptoid'] = 'Super-Adaptoid'
$champMap['aegon'] = 'Aegon'
$champMap['aeg'] = 'Aegon'
$champMap['agentvenom'] = 'Agent Venom'
$champMap['agv'] = 'Agent Venom'
$champMap['airwalker'] = 'Air-Walker'
$champMap['amcha'] = 'America Chavez'
$champMap['americachavez'] = 'America Chavez'
$champMap['anni'] = 'Annihilus'
$champMap['annihilus'] = 'Annihilus'
$champMap['antfu'] = 'Ant-Man (Future Variant)'
$champMap['antman'] = 'Ant-Man'
$champMap['antman_future'] = 'Ant-Man (Future)'
$champMap['antivenom'] = 'Anti-Venom'
$champMap['apocalypse'] = 'Apocalypse'
$champMap['apo'] = 'Apocalypse'
$champMap['ares'] = 'Ares'
$champMap['arcade'] = 'Arcade'
$champMap['arc'] = 'Arcade'
$champMap['archangel'] = 'Archangel'
$champMap['arnimzola'] = 'Arnim Zola'
$champMap['bast'] = 'Bast'
$champMap['beast'] = 'Beast'
$champMap['betaraybill'] = 'Beta Ray Bill'
$champMap['bishn'] = 'Bishop'
$champMap['bishop'] = 'Bishop'
$champMap['blade'] = 'Blade'
$champMap['blackbolt'] = 'Black Bolt'
$champMap['blumrvl'] = 'Blue Marvel'
$champMap['brothervoodoo'] = 'Brother Voodoo'
$champMap['bull'] = 'Bullseye'
$champMap['bullseye'] = 'Bullseye'
$champMap['cable'] = 'Cable'
$champMap['captainamerica_samwilson'] = 'Captain America (Sam Wilson)'
$champMap['capsw'] = 'Captain America (Sam Wilson)'
$champMap['captainbritain'] = 'Captain Britain'
$champMap['capb'] = 'Captain Britain'
$champMap['captainmarvel'] = 'Captain Marvel'
$champMap['carnage'] = 'Carnage'
$champMap['cassandranova'] = 'Cassandra Nova'
$champMap['cassie'] = 'Cassie Lang'
$champMap['champion'] = 'The Champion'
$champMap['thechamp'] = 'The Champion'
$champMap['civilwarrior'] = 'Civil Warrior'
$champMap['col'] = 'Colossus'
$champMap['colossus'] = 'Colossus'
$champMap['corvusglaive'] = 'Corvus Glaive'
$champMap['crv'] = 'Corvus Glaive'
$champMap['cullobsidian'] = 'Cull Obsidian'
$champMap['cyclops'] = 'Cyclops'
$champMap['cyclops_90s'] = 'Cyclops (90s)'
$champMap['cyc90'] = 'Cyclops (90s)'
$champMap['danimoonstar'] = 'Dani Moonstar'
$champMap['dani'] = 'Dani Moonstar'
$champMap['darkhawk'] = 'Darkhawk'
$champMap['dazzler'] = 'Dazzler'
$champMap['daz'] = 'Dazzler'
$champMap['deadpool'] = 'Deadpool'
$champMap['ded'] = 'Deadpool'
$champMap['deadpool_xforce'] = 'Deadpool (X-Force)'
$champMap['destroyer'] = 'Destroyer'
$champMap['diablo'] = 'Diablo'
$champMap['doc_ock'] = 'Doctor Octopus'
$champMap['doctordoom'] = 'Doctor Doom'
$champMap['doom'] = 'Doctor Doom'
$champMap['domino'] = 'Domino'
$champMap['dom'] = 'Domino'
$champMap['dormammu'] = 'Dormammu'
$champMap['dor'] = 'Dormammu'
$champMap['dracula'] = 'Dracula'
$champMap['drac'] = 'Dracula'
$champMap['drax'] = 'Drax'
$champMap['drstrange'] = 'Doctor Strange'
$champMap['dust'] = 'Dust'
$champMap['ebonymaw'] = 'Ebony Maw'
$champMap['elsa'] = 'Elsa Bloodstone'
$champMap['emmafrost'] = 'Emma Frost'
$champMap['emma'] = 'Emma Frost'
$champMap['enchantress'] = 'Enchantress'
$champMap['galan'] = 'Galan'
$champMap['gambit'] = 'Gambit'
$champMap['gamora'] = 'Gamora'
$champMap['gentle'] = 'Gentle'
$champMap['ghost'] = 'Ghost'
$champMap['ghostrider'] = 'Ghost Rider'
$champMap['gladiator'] = 'Gladiator'
$champMap['glad'] = 'Gladiator'
$champMap['gorr'] = 'Gorr the God Butcher'
$champMap['grandmaster'] = 'Grandmaster'
$champMap['gmast'] = 'Grandmaster'
$champMap['green_goblin'] = 'Green Goblin'
$champMap['groot'] = 'Groot'
$champMap['guardian'] = 'Guardian'
$champMap['guillotine'] = 'Guillotine'
$champMap['guillotine_2099'] = 'Guillotine 2099'
$champMap['havok'] = 'Havok'
$champMap['hvk'] = 'Havok'
$champMap['hela'] = 'Hela'
$champMap['heim'] = 'Heimdall'
$champMap['heimdall'] = 'Heimdall'
$champMap['herc'] = 'Hercules'
$champMap['hercules'] = 'Hercules'
$champMap['hitmon'] = 'Hit-Monkey'
$champMap['hitmonkey'] = 'Hit-Monkey'
$champMap['hlklng'] = 'Hulkling'
$champMap['hulkling'] = 'Hulkling'
$champMap['hulkbuster_movie'] = 'Hulkbuster'
$champMap['hulkim'] = 'Hulk (Immortal)'
$champMap['hulkrag'] = 'Hulk (Ragnarok)'
$champMap['hyp'] = 'Hyperion'
$champMap['hyperion'] = 'Hyperion'
$champMap['iceman'] = 'Iceman'
$champMap['icephoenix'] = 'Ice Phoenix'
$champMap['ikaris'] = 'Ikaris'
$champMap['iheart'] = 'Iron Heart'
$champMap['ironheart'] = 'Iron Heart'
$champMap['iim'] = 'Iron Man (Infamous)'
$champMap['ironman'] = 'Iron Man'
$champMap['ironman_infamous'] = 'Iron Man (Infamous)'
$champMap['ironman_silvercenturion'] = 'Iron Man (Silver Centurion)'
$champMap['ironfist'] = 'Iron Fist'
$champMap['ironpatriot'] = 'Iron Patriot'
$champMap['invwo'] = 'Invisible Woman'
$champMap['jeangrey'] = 'Jean Grey'
$champMap['jeangrey_current'] = 'Jean Grey (Current)'
$champMap['jess'] = 'Jessica Jones'
$champMap['jjj'] = 'J. Jonah Jameson'
$champMap['jjj_spiderslayer'] = 'J. Jonah Jameson (Spider-Slayer)'
$champMap['jubilee'] = 'Jubilee'
$champMap['jub'] = 'Jubilee'
$champMap['juggernaut'] = 'Juggernaut'
$champMap['kang'] = 'Kang'
$champMap['karlmordo'] = 'Karl Mordo'
$champMap['kate'] = 'Kate Bishop'
$champMap['kindred'] = 'Kindred'
$champMap['kittypryde'] = 'Kitty Pryde'
$champMap['knull'] = 'Knull'
$champMap['korg'] = 'Korg'
$champMap['kushala'] = 'Kushala'
$champMap['ktyp'] = 'King Thor'
$champMap['ld'] = 'Lady Deathstrike'
$champMap['ladydeathstrike'] = 'Lady Deathstrike'
$champMap['leader'] = 'The Leader'
$champMap['lockheed'] = 'Lockheed'
$champMap['lockjaw'] = 'Lockjaw'
$champMap['loki'] = 'Loki'
$champMap['longshot'] = 'Longshot'
$champMap['lotan'] = 'Leviathon Tide'
$champMap['luma'] = 'Luma'
$champMap['magik'] = 'Magik'
$champMap['magneto'] = 'Magneto'
$champMap['magneto_marvelnow'] = 'Magneto (Marvel Now)'
$champMap['mgnx'] = 'Magneto (X-Men)'
$champMap['maes'] = 'Maestro'
$champMap['maestro'] = 'Maestro'
$champMap['madelynepryor'] = 'Madelyne Pryor'
$champMap['mady'] = 'Madelyne Pryor'
$champMap['maker'] = 'The Maker'
$champMap['mangog'] = 'Mangog'
$champMap['manthing'] = 'Man-Thing'
$champMap['mantis'] = 'Mantis'
$champMap['medusa'] = 'Medusa'
$champMap['mephisto'] = 'Mephisto'
$champMap['mistersinister'] = 'Mister Sinister'
$champMap['mojo'] = 'Mojo'
$champMap['morningstar'] = 'Morningstar'
$champMap['msmarvel'] = 'Ms. Marvel'
$champMap['msmarvel_kamala'] = 'Ms. Marvel (Kamala Khan)'
$champMap['mysterio'] = 'Mysterio'
$champMap['mysto'] = 'Mysterio'
$champMap['nam'] = 'Namor'
$champMap['namor'] = 'Namor'
$champMap['nebula'] = 'Nebula'
$champMap['negasonicteenagewarhead'] = 'Negasonic Teenage Warhead'
$champMap['nicominoru'] = 'Nico Minoru'
$champMap['nico'] = 'Nico Minoru'
$champMap['nightcrawler'] = 'Nightcrawler'
$champMap['nim'] = 'Nimrod'
$champMap['nimrod'] = 'Nimrod'
$champMap['northstar'] = 'Northstar'
$champMap['nrthstr'] = 'Northstar'
$champMap['nova'] = 'Nova'
$champMap['odin'] = 'Odin'
$champMap['omegared'] = 'Omega Red'
$champMap['ore'] = 'Omega Red'
$champMap['omegasentinel'] = 'Omega Sentinel'
$champMap['onslaught'] = 'Onslaught'
$champMap['onslght'] = 'Onslaught'
$champMap['orochi'] = 'Orochi'
$champMap['peniparker'] = 'Peni Parker'
$champMap['peni'] = 'Peni Parker'
$champMap['phoenix'] = 'Phoenix'
$champMap['phx'] = 'Phoenix'
$champMap['phoenix_dark'] = 'Dark Phoenix'
$champMap['pixie'] = 'Pixie'
$champMap['professorx'] = 'Professor X'
$champMap['profx'] = 'Professor X'
$champMap['proximamidnight'] = 'Proxima Midnight'
$champMap['proxima'] = 'Proxima Midnight'
$champMap['prowler'] = 'Prowler'
$champMap['prowl'] = 'Prowler'
$champMap['psylocke'] = 'Psylocke'
$champMap['psymn'] = 'Psylocke'
$champMap['punisher_2099'] = 'Punisher 2099'
$champMap['pnshru'] = 'Punisher 2099'
$champMap['purgatory'] = 'Purgatory'
$champMap['purg'] = 'Purgatory'
$champMap['redskull'] = 'Red Skull'
$champMap['redg'] = 'Red Guardian'
$champMap['rgob'] = 'Red Goblin'
$champMap['red_goblin'] = 'Red Goblin'
$champMap['rintrah'] = 'Rintrah'
$champMap['rocket'] = 'Rocket Raccoon'
$champMap['rokt'] = 'Rocket Raccoon'
$champMap['rogue'] = 'Rogue'
$champMap['ronan'] = 'Ronan'
$champMap['rubythursday'] = 'Ruby Thursday'
$champMap['ruby'] = 'Ruby Thursday'
$champMap['sabretooth'] = 'Sabretooth'
$champMap['sand'] = 'Sandman'
$champMap['sasquatch'] = 'Sasquatch'
$champMap['sauron'] = 'Sauron'
$champMap['scarletwitch'] = 'Scarlet Witch'
$champMap['scream'] = 'Scream'
$champMap['scrm'] = 'Scream'
$champMap['sentinel'] = 'Sentinel'
$champMap['sentry'] = 'Sentry'
$champMap['sersi'] = 'Sersi'
$champMap['serpent'] = 'Serpent'
$champMap['shang'] = 'Shang-Chi'
$champMap['shocker'] = 'Shocker'
$champMap['shuri'] = 'Shuri'
$champMap['silk'] = 'Silk'
$champMap['silversurfer'] = 'Silver Surfer'
$champMap['surf'] = 'Silver Surfer'
$champMap['silversamurai'] = 'Silver Samurai'
$champMap['skrull'] = 'Skrull'
$champMap['solvarch'] = 'Solvang'
$champMap['solv'] = 'Solvang'
$champMap['sorcsup'] = 'Sorcerer Supreme'
$champMap['symbiotesupreme'] = 'Symbiote Supreme'
$champMap['spiderman'] = 'Spider-Man'
$champMap['spiral'] = 'Spiral'
$champMap['sprl'] = 'Spiral'
$champMap['starlord'] = 'Star-Lord'
$champMap['storm'] = 'Storm'
$champMap['stryfe'] = 'Stryfe'
$champMap['strf'] = 'Stryfe'
$champMap['sunspot'] = 'Sunspot'
$champMap['terrax'] = 'Terrax'
$champMap['terry'] = 'Terrax'
$champMap['thanos'] = 'Thanos'
$champMap['thor'] = 'Thor'
$champMap['thor_janefoster'] = 'Thor (Jane Foster)'
$champMap['tigra'] = 'Tigra'
$champMap['toad'] = 'Toad'
$champMap['tnia'] = 'Titania'
$champMap['torch'] = 'Human Torch'
$champMap['tm'] = 'Taskmaster'
$champMap['ultron'] = 'Ultron'
$champMap['ultron_prime'] = 'Ultron (Prime)'
$champMap['venom'] = 'Venom'
$champMap['venompool'] = 'Venompool'
$champMap['vtd'] = 'Venompool'
$champMap['venomtheduck'] = 'Venom the Duck'
$champMap['vision'] = 'Vision'
$champMap['vivvision'] = 'Viv Vision'
$champMap['viv'] = 'Viv Vision'
$champMap['vox'] = 'Vox'
$champMap['vulture_movie'] = 'Vulture'
$champMap['warmachine'] = 'War Machine'
$champMap['warmac'] = 'War Machine'
$champMap['warlock'] = 'Warlock'
$champMap['wrlk'] = 'Warlock'
$champMap['wave'] = 'Wave'
$champMap['werewolfbynight'] = 'Werewolf by Night'
$champMap['wwolf'] = 'Werewolf by Night'
$champMap['whitetiger'] = 'White Tiger'
$champMap['whttgr'] = 'White Tiger'
$champMap['wiccan'] = 'Wiccan'
$champMap['wolverine'] = 'Wolverine'
$champMap['wolverine_oldman'] = 'Old Man Logan'
$champMap['osntl'] = 'Old Man Logan'
$champMap['wolverine_weaponx'] = 'Wolverine (Weapon X)'
$champMap['wolverine_xforce'] = 'Wolverine (X-Force)'
$champMap['wong'] = 'Wong'
$champMap['x23'] = 'X-23'
$champMap['x23_legacy'] = 'X-23 (Uncanny)'
$champMap['x23u'] = 'X-23 (Uncanny)'
$champMap['ylb'] = 'Yellowjacket'
$champMap['yondu'] = 'Yondu'
$champMap['zemo'] = 'Baron Zemo'
$champMap['zola'] = 'Arnim Zola'
$champMap['kang'] = 'Kang'
$champMap['kangimp'] = 'Kang (Impostor)'
$champMap['kangsup'] = 'Kang (Superior)'

# ===== 3.1. 既知クラスの補完マップ (BCGバイナリに定義なしの旧チャンピオン) =====
$knownClass = @{
    # Science
    'abomination'='science'; 'abim'='science'; 'absorbing'='science'; 'absorbingman'='science'
    'agv'='science'; 'agentvenom'='science'; 'antman'='science'; 'antm'='science'; 'antu'='science'
    'blackwidow'='science'; 'blkwidw'='science'; 'blkwidow'='science'; 'bwmcu'='science'; 'cvbw'='science'
    'blumrvl'='science'; 'bluemarvel'='science'
    'cassie'='science'; 'cassielang'='science'
    'electro'='science'; 'elec'='science'; 'elecluke'='science'
    'hulk'='science'; 'hulkim'='science'; 'hulkrag'='science'; 'hulku'='science'
    'invwo'='science'; 'invisiblewoman'='science'
    'jess'='science'; 'jessicajones'='science'
    'lizard'='science'; 'lzrd'='science'
    'luke'='science'; 'lukecase'='science'
    'maestro'='science'; 'maes'='science'
    'morb'='science'; 'morbius'='science'
    'mr_fantastic'='science'; 'reed'='science'
    'rhino'='science'; 'rhno'='science'
    'sand'='science'; 'sandman'='science'
    'sentry'='cosmic'  # Sentry is actually Cosmic
    'tnia'='science'; 'titania'='science'
    'torch'='science'; 'humantorch'='science'
    'thing'='science'
    'theleader'='science'; 'leader'='science'
    'venom'='science'; 'vnm'='science'
    'venompool'='science'; 'vnpl'='science'
    'venomtheduck'='science'
    'wave'='science'
    # Skill
    'ares'='skill'
    'blade'='skill'; 'bladesf'='skill'
    'bull'='skill'; 'bullseye'='skill'
    'crossbones'='skill'; 'crbu'='skill'
    'daredevil'='skill'; 'drdn'='skill'; 'drdvl'='skill'; 'ddpl'='skill'
    'elektra'='skill'
    'elsa'='skill'; 'elsabloodstone'='skill'
    'hawkeye'='skill'; 'hawko'='skill'; 'hawky'='skill'; 'hwky'='skill'
    'hitmon'='skill'; 'hitmonkey'='skill'
    'jjj'='skill'; 'jjonahjameson'='skill'
    'kate'='skill'; 'katebishop'='skill'
    'mbaku'='skill'
    'moonknight'='skill'; 'mk'='skill'; 'mkt'='skill'
    'msmarvel'='skill'; 'msmrvl'='skill'
    'nickfury'='skill'; 'nick'='skill'
    'psych'='skill'; 'psyl'='skill'
    'punisher'='skill'; 'pnshr'='skill'; 'pnsher'='skill'; 'pn29'='skill'; 'pn29u'='skill'
    'shang'='skill'; 'shangchi'='skill'
    'silk'='skill'
    'spot'='skill'
    'taskmaster'='skill'; 'tm'='skill'
    'yellowjacket'='skill'; 'ylb'='skill'; 'ylj'='skill'; 'yllwjac'='skill'
    # Tech
    'arnimzola'='tech'; 'zola'='tech'
    'baron_zemo'='tech'; 'zemo'='tech'
    'darkhawk'='tech'; 'dhawk'='tech'; 'dhark'='tech'; 'dhk'='tech'
    'destroyer'='tech'
    'ghostrider_robbie'='tech'
    'hkbst'='tech'; 'hulkbstr'='tech'; 'hulkbuster'='tech'
    'ironman_infamous'='tech'; 'iim'='tech'; 'imi'='tech'
    'ironpatriot'='tech'
    'antfu'='tech'; 'antman_future'='tech'
    'jjj_spiderslayer'='tech'
    'kang'='tech'; 'kangimp'='tech'; 'kangsup'='tech'; 'kng'='tech'
    'korg'='tech'
    'leader_armored'='tech'
    'proxima'='tech'
    'redg'='tech'; 'redguardian'='tech'
    'rokt'='tech'; 'rocketraccoon'='tech'
    'sentinel'='tech'; 'sent'='tech'; 'sentibot'='tech'
    'shocker'='tech'; 'shkr'='tech'
    'visionaark'='tech'; 'visaark'='tech'; 'vsn'='tech'
    'warmac'='tech'; 'warmachine'='tech'
    'ylb_yellow'='tech'
    # Mystic
    'aeg'='mystic'; 'aegon'='mystic'
    'bast'='mystic'
    'blackwitchknife'='mystic'
    'doctor_voodoo'='mystic'; 'drvood'='mystic'
    'ifist'='mystic'; 'ifistw'='mystic'; 'ironfist'='mystic'; 'ironfist_white'='mystic'
    'karlmordo'='mystic'; 'karl'='mystic'; 'mordo'='mystic'
    'ktyp'='cosmic'  # King Thor is actually Cosmic
    'loki'='mystic'
    'mantis'='mystic'
    'medus'='mystic'; 'medusa'='mystic'
    'meph'='mystic'; 'mephis'='mystic'; 'mephisto'='mystic'
    'mrkn'='mystic'; 'moondragon'='mystic'; 'moondr'='mystic'
    'sorcsup'='mystic'; 'sorcerersupreme'='mystic'
    'symbiote_supreme'='mystic'; 'sym'='mystic'; 'syms'='mystic'
    'thor_jane'='mystic'; 'thrj'='mystic'
    'void'='mystic'
    'wong'='mystic'
    # Cosmic
    'adam'='cosmic'; 'adamwarlock'='cosmic'
    'angela'='cosmic'; 'ang'='cosmic'
    'annihilus'='cosmic'; 'anni'='cosmic'
    'corvus'='cosmic'; 'corvusglaive'='cosmic'
    'cullobsidian'='cosmic'; 'cul'='cosmic'
    'darkphoenix'='cosmic'; 'dkphnx'='cosmic'
    'galan'='cosmic'
    'ikaris'='cosmic'
    'knull'='cosmic'
    'ms_marvel'='cosmic'; 'captain_marvel'='cosmic'
    'sentry_void'='cosmic'
    'silver_surfer'='cosmic'
    'thanos'='cosmic'
    'thechamp'='cosmic'; 'champion'='cosmic'
    'thor'='cosmic'; 'thrh'='cosmic'; 'thru'='cosmic'
    'valkyr'='cosmic'; 'valk'='cosmic'
    'x23u'='mutant'  # X-23 Uncanny is Mutant
    # Mutant
    'mgnx'='mutant'; 'magneto_xmen'='mutant'
    'osntl'='mutant'; 'wolverine_oldman'='mutant'
    'qckslvr'='mutant'; 'quicksilver'='mutant'
    'sabre'='mutant'; 'sabretooth'='mutant'
    'storm'='mutant'; 'strm'='mutant'; 'stormr'='mutant'
    'x230'='mutant'; 'x231'='mutant'
}

# ===== 3.5. プレフィックス→クラス変換テーブルを構築 =====
# champClassは定義ID(onslaught)を持つが、BCGプレフィックス(onslght)と一致しない場合がある
# champMapを経由して「表示名 → 正規化 → クラス」で解決する
$classInvMap = @{}  # 正規化された定義ID → クラス
foreach ($kv in $champClass.GetEnumerator()) {
    $norm = $kv.Key -replace '[^a-z0-9]', ''
    $classInvMap[$norm] = $kv.Value
}
$prefixClass = @{}
foreach ($kv in $champClass.GetEnumerator()) { $prefixClass[$kv.Key] = $kv.Value }
foreach ($kv in $knownClass.GetEnumerator()) {
    if (-not $prefixClass.ContainsKey($kv.Key)) { $prefixClass[$kv.Key] = $kv.Value }
}
foreach ($kv in $champMap.GetEnumerator()) {
    $pfx = $kv.Key
    if ($prefixClass.ContainsKey($pfx)) { continue }
    # 表示名を正規化してclassInvMapで検索
    $norm = ($kv.Value -replace '[^a-zA-Z0-9]', '').ToLower()
    if ($classInvMap.ContainsKey($norm)) { $prefixClass[$pfx] = $classInvMap[$norm] }
}

# ===== 4. チャンピオンごとにグループ化 =====
Write-Host "グループ化中..."
$groups = $entries | Group-Object { ($_.Id -split '_')[0] } | Sort-Object Name

# ===== 5. ファイル出力 =====
Write-Host "ファイル書き込み中..."
$sw = [System.IO.StreamWriter]::new($outFile, $false, [System.Text.Encoding]::UTF8)
$eq80 = "=" * 80
$dsh60 = "-" * 60

$sw.WriteLine($eq80)
$sw.WriteLine("Marvel Contest of Champions - チャンピオン全能力データ")
$sw.WriteLine("ソース: B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin")
$sw.WriteLine("総エントリー数: $($entries.Count)  |  チャンピオン数: $($groups.Count)")
$sw.WriteLine($eq80)

foreach ($grp in $groups) {
    $prefix = $grp.Name
    $fullName = if ($champMap.ContainsKey($prefix)) { $champMap[$prefix] }
                elseif ($champClass.ContainsKey($prefix)) { $prefix }
                else { $prefix }
    $cls = if ($prefixClass.ContainsKey($prefix)) { $prefixClass[$prefix].ToUpper() } else { "?" }

    $all = $grp.Group | Sort-Object { $_.Id }
    $sigEntries = $all | Where-Object { $_.Id -match '_sig_|_sig$|_awaken' }
    $sp1Entries = $all | Where-Object { $_.Id -match '_sp1_|_sp1$' }
    $sp2Entries = $all | Where-Object { $_.Id -match '_sp2_|_sp2$' }
    $sp3Entries = $all | Where-Object { $_.Id -match '_sp3_|_sp3$' }
    $synEntries = $all | Where-Object { $_.Id -match '_syn_|_syn$' }
    $otherEntries = $all | Where-Object {
        $_.Id -notmatch '_sig_|_sig$|_awaken|_sp1_|_sp1$|_sp2_|_sp2$|_sp3_|_sp3$|_syn_|_syn$'
    }

    $sw.WriteLine("")
    $sw.WriteLine($eq80)
    $sw.WriteLine("チャンピオン: $fullName  [$prefix]  クラス: $cls  (計$($all.Count)エントリー)")
    $sw.WriteLine($eq80)

    function Write-Section($label, $eList, $sw, $dsh60) {
        if (-not $eList -or @($eList).Count -eq 0) { return }
        $sw.WriteLine("")
        $sw.WriteLine("  [$label] ($(@($eList).Count)件)")
        $sw.WriteLine("  " + $dsh60)
        foreach ($e in $eList) {
            $v1 = if ($null -ne $e.V1) { [math]::Round($e.V1,4).ToString() } else { "" }
            $v2 = if ($null -ne $e.V2) { [math]::Round($e.V2,4).ToString() } else { "" }
            $v3 = if ($null -ne $e.V3) { [math]::Round($e.V3,4).ToString() } else { "" }
            $line = "    " + $e.Id.PadRight(48) + $e.Type.PadRight(22) + $e.Trigger.PadRight(22) + $v1.PadRight(10) + $v2.PadRight(10) + $v3
            $sw.WriteLine($line)
            if ($e.Condition -ne "" -and $e.Condition.Length -lt 300) { $sw.WriteLine("      条件: " + $e.Condition) }
            if ($e.Filter -ne "" -and $e.Filter.Length -lt 300) { $sw.WriteLine("      フィルター: " + $e.Filter) }
            if ($e.Var -ne "") { $sw.WriteLine("      変数: " + $e.Var) }
        }
    }

    Write-Section "シグネチャー(覚醒)" $sigEntries $sw $dsh60
    Write-Section "通常能力/パッシブ" $otherEntries $sw $dsh60
    Write-Section "必殺技1 (SP1)" $sp1Entries $sw $dsh60
    Write-Section "必殺技2 (SP2)" $sp2Entries $sw $dsh60
    Write-Section "必殺技3 (SP3)" $sp3Entries $sw $dsh60
    Write-Section "シナジーボーナス" $synEntries $sw $dsh60
}
$sw.Close()

$fi = Get-Item $outFile
$sizeMB = [math]::Round($fi.Length / 1048576, 2)
Write-Host "完了: $outFile ($sizeMB MB)"
