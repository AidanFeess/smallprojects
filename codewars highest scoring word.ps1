$AZ = [char[]](65..90)

function Get-CalculatedScore($str){
    $ttl = 0
    for(($i=0); $i -lt $str.Length; $i++){
        $ttl += $AZ.IndexOf([char]([string]$str[$i]).ToUpper())+1
    }
    return $ttl
}

function Get-HighestScoringWord([string]$s){
    $a = $s.Split(" ")
    $finalword = $a[0]
    $highscore = Get-CalculatedScore $a[0]
    foreach($word in $a){
        $newscore = Get-CalculatedScore $word
        if($newscore -gt $highscore){
            $highscore = $newscore
            $finalword = $word
        }
    }
    return $finalword
}