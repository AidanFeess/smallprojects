function Get-SumOfPositive($NumberArray)
{
    $total = 0
    for (($i=0); $i -lt $NumberArray.Length; $i++){
        if ($NumberArray[$i] -lt 0){
            continue
        }
        $total += $NumberArray[$i]
    }
    return $total
}