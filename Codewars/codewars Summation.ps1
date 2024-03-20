function Summation([int] $n) {
    $sum=0
    for(($n); $n -gt 0; $n--){
        $sum+=$n
    }
    return $sum
  }