function Get-SumOfMultiples($i){
    $st=$i
    $ttl=0
    for(($i); $i -gt 0; $i--){
        if($i%3 -eq 0 -or $i%5 -eq 0){
            $ttl += $i
        }
    }
    
    return $ttl - $st
}

Get-SumOfMultiples(6)